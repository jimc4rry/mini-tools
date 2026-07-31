import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.billing.models import Subscription

from .forms import ClientForm, InvoiceForm, InvoiceItemFormSet
from .models import INVOICING_TRIAL_LENGTH_DAYS, Client, Invoice


def _ensure_subscription(user):
    """
    Unlike Vault/Wellness, Invoicing has no profile data to collect up front
    (no PIN, no health stats) - so there's no separate onboarding step. The
    trial Subscription is just created lazily on first visit.
    """
    Subscription.objects.get_or_create(
        user=user,
        product="invoicing",
        defaults={
            "trial_ends_at": timezone.localdate()
            + datetime.timedelta(days=INVOICING_TRIAL_LENGTH_DAYS)
        },
    )


@login_required
def dashboard(request):
    _ensure_subscription(request.user)

    invoices = Invoice.objects.filter(owner=request.user).select_related("client")
    outstanding = sum(
        (inv.total for inv in invoices if inv.status == Invoice.Status.SENT), start=0
    )
    overdue = [inv for inv in invoices if inv.is_overdue]
    paid_this_month = sum(
        (
            inv.total
            for inv in invoices
            if inv.status == Invoice.Status.PAID
            and inv.updated_at.month == timezone.localdate().month
            and inv.updated_at.year == timezone.localdate().year
        ),
        start=0,
    )

    context = {
        "invoices": invoices[:20],
        "outstanding": outstanding,
        "overdue": overdue,
        "paid_this_month": paid_this_month,
        "client_count": Client.objects.filter(owner=request.user).count(),
    }
    return render(request, "invoicing/dashboard.html", context)


@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, "invoicing/client_list.html", {"clients": clients})


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            messages.success(request, _("Client added."))
            return redirect("invoicing:client_list")
    else:
        form = ClientForm()
    return render(request, "invoicing/client_form.html", {"form": form, "is_new": True})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, _("Client updated."))
            return redirect("invoicing:client_list")
    else:
        form = ClientForm(instance=client)
    return render(request, "invoicing/client_form.html", {"form": form, "is_new": False})


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        try:
            client.delete()
        except ProtectedError:
            messages.error(
                request,
                _("Can't delete this client - they still have invoices. Delete those first."),
            )
            return redirect("invoicing:client_list")
        messages.success(request, _("Client deleted."))
        return redirect("invoicing:client_list")
    return render(request, "invoicing/client_confirm_delete.html", {"client": client})


@login_required
def invoice_create(request):
    if not Client.objects.filter(owner=request.user).exists():
        messages.info(request, _("Add a client first."))
        return redirect("invoicing:client_create")

    if request.method == "POST":
        form = InvoiceForm(request.POST, owner=request.user)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.owner = request.user
            invoice.number = Invoice.next_number(request.user, invoice.kind)
            invoice.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, _("Invoice created."))
            return redirect("invoicing:dashboard")
    else:
        today = timezone.localdate()
        form = InvoiceForm(
            owner=request.user,
            initial={"issue_date": today, "due_date": today + datetime.timedelta(days=14)},
        )
        formset = InvoiceItemFormSet()
    return render(
        request, "invoicing/invoice_form.html", {"form": form, "formset": formset, "is_new": True}
    )


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, owner=request.user)
        formset = InvoiceItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _("Invoice updated."))
            return redirect("invoicing:dashboard")
    else:
        form = InvoiceForm(instance=invoice, owner=request.user)
        formset = InvoiceItemFormSet(instance=invoice)
    return render(
        request,
        "invoicing/invoice_form.html",
        {"form": form, "formset": formset, "is_new": False, "invoice": invoice},
    )


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    if request.method == "POST":
        invoice.delete()
        messages.success(request, _("Invoice deleted."))
        return redirect("invoicing:dashboard")
    return render(request, "invoicing/invoice_confirm_delete.html", {"invoice": invoice})


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("client").prefetch_related("items"),
        pk=pk,
        owner=request.user,
    )
    return render(request, "invoicing/invoice_print.html", {"invoice": invoice})


@login_required
@require_POST
def invoice_mark_sent(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    invoice.status = Invoice.Status.SENT
    invoice.save(update_fields=["status", "updated_at"])
    messages.success(request, _("Marked as sent."))
    return redirect("invoicing:dashboard")


@login_required
@require_POST
def invoice_mark_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    invoice.status = Invoice.Status.PAID
    invoice.save(update_fields=["status", "updated_at"])
    messages.success(request, _("Marked as paid."))
    return redirect("invoicing:dashboard")


@login_required
@require_POST
def invoice_cancel(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    invoice.status = Invoice.Status.CANCELLED
    invoice.save(update_fields=["status", "updated_at"])
    messages.success(request, _("Cancelled."))
    return redirect("invoicing:dashboard")
