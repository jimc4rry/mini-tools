import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.billing.models import Subscription
from apps.core.ratelimit import is_rate_limited

from .forms import ChangePinForm, UnlockForm, VaultItemForm, VaultOnboardingForm
from .models import VAULT_TRIAL_ITEM_LIMIT, VaultItem, VaultProfile

UNLOCK_WINDOW_MINUTES = 10
UNLOCK_MAX_ATTEMPTS = 5
UNLOCK_WINDOW_SECONDS = 300


def _profile_or_none(user):
    try:
        return user.vault_profile
    except VaultProfile.DoesNotExist:
        return None


def _redirect_no_profile(request):
    if request.user.is_superuser:
        messages.info(request, _("This account isn't set up with a Vault yet."))
        return redirect("platform_admin:dashboard")
    if request.user.is_staff:
        messages.info(request, _("This account isn't set up with a Vault yet."))
        return redirect("/admin/")
    return redirect("vault:start_trial")


def _is_unlocked(request):
    unlocked_at = request.session.get("vault_unlocked_at")
    if not unlocked_at:
        return False
    try:
        unlocked_at = datetime.datetime.fromisoformat(unlocked_at)
    except ValueError:
        return False
    return timezone.now() - unlocked_at < datetime.timedelta(minutes=UNLOCK_WINDOW_MINUTES)


@login_required
def start_trial(request):
    """
    Sets up a Master PIN and starts the Vault free trial for a platform
    account that doesn't have one yet (mirrors apps.tracker.views.start_trial).
    """
    if _profile_or_none(request.user):
        return redirect("vault:dashboard")

    if request.method == "POST":
        form = VaultOnboardingForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, _("Welcome! Your Vault is ready."))
            return redirect("vault:dashboard")
    else:
        form = VaultOnboardingForm()
    return render(request, "vault/start_trial.html", {"form": form})


@login_required
def dashboard(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return _redirect_no_profile(request)

    items = VaultItem.objects.filter(owner=request.user, is_active=True)

    soon_cutoff = timezone.localdate() + datetime.timedelta(days=30)
    expiring_soon = items.filter(expires_at__isnull=False, expires_at__lte=soon_cutoff).order_by(
        "expires_at"
    )

    monthly_total = 0
    annual_total = 0
    for item in items:
        if item.cost_amount is None:
            continue
        if item.billing_cycle == VaultItem.BillingCycle.MONTHLY:
            monthly_total += item.cost_amount
            annual_total += item.cost_amount * 12
        elif item.billing_cycle == VaultItem.BillingCycle.ANNUAL:
            annual_total += item.cost_amount
            monthly_total += item.cost_amount / 12

    context = {
        "items": items,
        "expiring_soon": expiring_soon,
        "monthly_total": round(monthly_total, 2),
        "annual_total": round(annual_total, 2),
        "is_unlocked": _is_unlocked(request),
        "trial_item_limit": VAULT_TRIAL_ITEM_LIMIT,
        "is_active_subscriber": Subscription.is_active_for(request.user, "vault"),
    }
    return render(request, "vault/dashboard.html", context)


@login_required
def item_create(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return _redirect_no_profile(request)

    existing_count = VaultItem.objects.filter(owner=request.user, is_active=True).count()
    limit_reached = (
        existing_count >= VAULT_TRIAL_ITEM_LIMIT
        and not Subscription.is_active_for(request.user, "vault")
    )
    if limit_reached:
        messages.error(
            request,
            _("You've reached the %(limit)d-item trial limit. Upgrade to add more.")
            % {"limit": VAULT_TRIAL_ITEM_LIMIT},
        )
        return redirect("vault:dashboard")

    if request.method == "POST":
        form = VaultItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            messages.success(request, _("Item added."))
            return redirect("vault:dashboard")
    else:
        form = VaultItemForm()
    return render(request, "vault/item_form.html", {"form": form, "is_new": True})


@login_required
def item_edit(request, pk):
    item = get_object_or_404(VaultItem, pk=pk, owner=request.user)
    if request.method == "POST":
        form = VaultItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, _("Item updated."))
            return redirect("vault:dashboard")
    else:
        form = VaultItemForm(instance=item)
    return render(request, "vault/item_form.html", {"form": form, "is_new": False, "item": item})


@login_required
def item_delete(request, pk):
    item = get_object_or_404(VaultItem, pk=pk, owner=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, _("Item deleted."))
        return redirect("vault:dashboard")
    return render(request, "vault/item_confirm_delete.html", {"item": item})


@login_required
def unlock(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return _redirect_no_profile(request)

    if request.method == "POST":
        if is_rate_limited(
            request,
            f"vault_unlock:{request.user.id}",
            max_requests=UNLOCK_MAX_ATTEMPTS,
            window_seconds=UNLOCK_WINDOW_SECONDS,
        ):
            messages.error(request, _("Too many attempts. Please try again in a few minutes."))
            return redirect("vault:dashboard")

        form = UnlockForm(request.POST)
        if form.is_valid() and check_password(form.cleaned_data["pin"], profile.pin_hash):
            request.session["vault_unlocked_at"] = timezone.now().isoformat()
            messages.success(request, _("Vault unlocked."))
        else:
            messages.error(request, _("Incorrect PIN."))
    return redirect("vault:dashboard")


@login_required
def reveal_item(request, pk):
    item = get_object_or_404(VaultItem, pk=pk, owner=request.user)
    if not _is_unlocked(request):
        return JsonResponse({"locked": True}, status=403)
    return JsonResponse({"secret_value": item.secret_value})


@login_required
def settings_view(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return _redirect_no_profile(request)

    if request.method == "POST":
        form = ChangePinForm(request.POST, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, _("PIN updated."))
            return redirect("vault:settings")
    else:
        form = ChangePinForm(profile=profile)
    return render(request, "vault/settings.html", {"form": form})
