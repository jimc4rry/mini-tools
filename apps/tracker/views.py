import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from .forms import BusinessOnboardingForm, CategoryForm, InventoryItemForm, NotificationSettingsForm
from .models import Business, Category, InventoryItem, Product


def _business_or_none(user):
    try:
        return user.business
    except Business.DoesNotExist:
        return None


def _redirect_no_business(request):
    if request.user.is_superuser:
        messages.info(request, _("This account isn't linked to a business."))
        return redirect("platform_admin:dashboard")
    if request.user.is_staff:
        messages.info(request, _("This account isn't linked to a business."))
        return redirect("/admin/")
    return redirect("start_trial")


@login_required
def start_trial(request):
    """
    Starts the Expiration Tracker free trial for a platform account that
    doesn't have one yet - reached either directly, or bounced here from
    dashboard() via _redirect_no_business().
    """
    if _business_or_none(request.user):
        return redirect("dashboard")

    if request.method == "POST":
        form = BusinessOnboardingForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, _("Welcome! Your free trial has started."))
            return redirect("dashboard")
    else:
        form = BusinessOnboardingForm()
    return render(request, "tracker/start_trial.html", {"form": form})


@login_required
def dashboard(request):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    active_items = business.inventory_items.filter(
        status=InventoryItem.Status.ACTIVE
    ).select_related("product")

    filter_urgency = request.GET.get("urgency")
    search_query = request.GET.get("q", "").strip()

    items = list(active_items)
    if filter_urgency:
        items = [i for i in items if i.urgency == filter_urgency]
    if search_query:
        q = search_query.lower()
        items = [
            i for i in items
            if q in (i.product.barcode or "").lower() or q in i.product.name.lower()
        ]

    counts = {"expired": 0, "critical": 0, "warning": 0, "ok": 0}
    for item in active_items:
        counts[item.urgency] += 1

    low_stock_products = [p for p in business.products.filter(is_active=True) if p.is_low_stock]

    return render(
        request,
        "tracker/dashboard.html",
        {
            "business": business,
            "items": items,
            "counts": counts,
            "active_filter": filter_urgency,
            "search_query": search_query,
            "low_stock_products": low_stock_products,
        },
    )


@login_required
def item_create(request):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    if request.method == "POST":
        form = InventoryItemForm(request.POST, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, _("Product added."))
            return redirect("dashboard")
    else:
        form = InventoryItemForm(business=business)
    return render(request, "tracker/item_form.html", {"form": form, "title": _("Add product")})


@login_required
def item_edit(request, pk):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    item = get_object_or_404(InventoryItem, pk=pk, business=business)
    if request.method == "POST":
        form = InventoryItemForm(request.POST, instance=item, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, _("Product updated."))
            return redirect("dashboard")
    else:
        form = InventoryItemForm(instance=item, business=business)
    return render(request, "tracker/item_form.html", {"form": form, "title": _("Edit product")})


@login_required
def item_delete(request, pk):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    item = get_object_or_404(InventoryItem, pk=pk, business=business)
    if request.method == "POST":
        item.delete()
        messages.success(request, _("Product deleted."))
        return redirect("dashboard")
    return render(request, "tracker/item_confirm_delete.html", {"item": item})


@login_required
def item_consume(request, pk):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    item = get_object_or_404(
        InventoryItem, pk=pk, business=business, status=InventoryItem.Status.ACTIVE
    )
    if request.method == "POST":
        item.quantity -= 1
        if item.quantity <= 0:
            item.quantity = 0
            item.status = InventoryItem.Status.CONSUMED
            item.resolved_at = timezone.now()
        item.save()
        messages.success(request, _("Quantity updated."))
    return redirect("dashboard")


@login_required
def item_waste(request, pk):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    item = get_object_or_404(
        InventoryItem, pk=pk, business=business, status=InventoryItem.Status.ACTIVE
    )
    if request.method == "POST":
        item.status = InventoryItem.Status.WASTED
        item.resolved_at = timezone.now()
        item.save()
        messages.success(request, _("Recorded as waste."))
    return redirect("dashboard")


@login_required
def waste_log(request):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    items = list(
        business.inventory_items.filter(status=InventoryItem.Status.WASTED)
        .select_related("product")
        .order_by("-resolved_at")
    )

    month_start = timezone.localdate().replace(day=1)
    this_month_items = [i for i in items if i.resolved_at and i.resolved_at.date() >= month_start]
    month_value = sum(
        (i.waste_value for i in this_month_items if i.waste_value is not None), Decimal("0")
    )

    return render(
        request,
        "tracker/waste_log.html",
        {
            "items": items,
            "month_count": len(this_month_items),
            "month_value": month_value,
        },
    )


@login_required
def export_csv(request):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    items = business.inventory_items.filter(
        status=InventoryItem.Status.ACTIVE
    ).select_related("product", "product__category")

    filter_urgency = request.GET.get("urgency")
    search_query = request.GET.get("q", "").strip()

    items = list(items)
    if filter_urgency:
        items = [i for i in items if i.urgency == filter_urgency]
    if search_query:
        q = search_query.lower()
        items = [
            i for i in items
            if q in (i.product.barcode or "").lower() or q in i.product.name.lower()
        ]

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    filename = f"inventory_{timezone.localdate()}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(
        [
            _("Product"), "Barcode", _("Category"), _("Quantity"), _("Unit"),
            _("Expiration date"), _("Days"), _("Status"), "Batch", _("Notes"),
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.product.name,
                item.product.barcode,
                item.product.category.name if item.product.category else "",
                item.quantity,
                item.product.get_unit_display(),
                item.expiration_date.strftime("%d/%m/%Y"),
                item.days_left,
                item.urgency,
                item.batch_number,
                item.notes,
            ]
        )
    return response


@login_required
def barcode_lookup(request):
    business = _business_or_none(request.user)
    if business is None:
        return JsonResponse({"found": False}, status=404)
    code = request.GET.get("code", "").strip()
    if not code:
        return JsonResponse({"found": False})
    product = Product.objects.filter(business=business, barcode=code, is_active=True).first()
    if not product:
        return JsonResponse({"found": False})
    active_batches = product.inventory_items.filter(status=InventoryItem.Status.ACTIVE).count()
    return JsonResponse(
        {
            "found": True,
            "name": product.name,
            "category_id": product.category_id,
            "unit": product.unit,
            "unit_cost": str(product.unit_cost) if product.unit_cost is not None else "",
            "min_required_quantity": (
                str(product.min_required_quantity) if product.min_required_quantity is not None else ""
            ),
            "active_batches": active_batches,
        }
    )


@login_required
def category_list(request):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    if request.method == "POST":
        form = CategoryForm(request.POST, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category added."))
            return redirect("category_list")
    else:
        form = CategoryForm(business=business)
    categories = business.categories.filter(is_active=True)
    return render(request, "tracker/categories.html", {"form": form, "categories": categories})


@login_required
def category_delete(request, pk):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    category = get_object_or_404(Category, pk=pk, business=business)
    if request.method == "POST":
        category.is_active = False
        category.save()
        messages.success(request, _("Category deleted."))
    return redirect("category_list")


@login_required
def settings_view(request):
    business = _business_or_none(request.user)
    if business is None:
        return _redirect_no_business(request)
    if request.method == "POST":
        form = NotificationSettingsForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, _("Notification settings updated."))
            return redirect("settings")
    else:
        form = NotificationSettingsForm(instance=business)
    return render(request, "tracker/settings.html", {"form": form, "business": business})
