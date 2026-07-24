from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from apps.billing.forms import PlatformSubscriptionForm
from apps.billing.models import Subscription
from apps.billing.webhooks import sync_tracker_business
from apps.feedback.models import Feedback


def platform_admin_required(view_func):
    """Restricts a view to Django superusers - the Hub operator's own
    cross-app support/billing panel, separate from any one app's own
    per-user permissions (e.g. Tracker's own staff/business roles)."""
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("You do not have access to this page.")
        return view_func(request, *args, **kwargs)
    return wrapper


@platform_admin_required
def dashboard(request):
    """Cross-app list of every subscription on the platform (one row per
    user+product), for support/billing purposes - the generic counterpart
    to Django admin's per-model views, which have no cross-app overview."""
    subscriptions = Subscription.objects.select_related("user").order_by("-updated_at")

    product_filter = request.GET.get("product", "").strip()
    if product_filter:
        subscriptions = subscriptions.filter(product=product_filter)

    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)

    search_query = request.GET.get("q", "").strip()
    if search_query:
        subscriptions = subscriptions.filter(
            Q(user__username__icontains=search_query) | Q(user__email__icontains=search_query)
        )

    page_obj = Paginator(subscriptions, 20).get_page(request.GET.get("page"))

    products = Subscription.objects.order_by("product").values_list("product", flat=True).distinct()

    context = {
        "subscriptions": page_obj,
        "page_obj": page_obj,
        "product_filter": product_filter,
        "status_filter": status_filter,
        "search_query": search_query,
        "products": products,
        "status_choices": Subscription.Status.choices,
        "total_count": Subscription.objects.count(),
        "active_count": Subscription.objects.filter(status=Subscription.Status.ACTIVE).count(),
        "trial_count": Subscription.objects.filter(status=Subscription.Status.TRIAL).count(),
        # unread_feedback_count itself comes from apps.feedback's context
        # processor (runs for every superuser request) - just the list here.
        "recent_feedback": Feedback.objects.order_by("-created_at")[:10],
    }
    return render(request, "platform_admin/dashboard.html", context)


@platform_admin_required
def subscription_detail(request, pk):
    """Support view for one subscription - lets the platform operator record
    plan changes by hand, for cases outside the normal Paddle flow (no real
    Paddle account is wired up yet, so this is currently the only way to
    activate/change a plan)."""
    subscription = get_object_or_404(Subscription.objects.select_related("user"), pk=pk)

    if request.method == "POST":
        form = PlatformSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            sync_tracker_business(subscription)
            messages.success(request, _("Subscription updated."))
            return redirect("platform_admin:subscription_detail", pk=subscription.pk)
    else:
        form = PlatformSubscriptionForm(instance=subscription)

    business = None
    if subscription.product == "tracker":
        from apps.tracker.models import Business
        business = Business.objects.filter(owner=subscription.user).first()

    context = {
        "subscription": subscription,
        "form": form,
        "business": business,
    }
    return render(request, "platform_admin/subscription_detail.html", context)


@platform_admin_required
def feedback_detail(request, pk):
    """Full view of one submission, without leaving Platform Admin for the
    Django admin. Opening it (GET) marks it read, same as the admin change
    page does - a POST here is only ever the delete button."""
    feedback = get_object_or_404(Feedback, pk=pk)

    if request.method == "POST":
        feedback.delete()
        messages.success(request, _("Feedback deleted."))
        return redirect("platform_admin:dashboard")

    if not feedback.is_read:
        feedback.is_read = True
        feedback.save(update_fields=["is_read"])

    return render(request, "platform_admin/feedback_detail.html", {"feedback": feedback})
