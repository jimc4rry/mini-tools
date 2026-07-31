from django.utils import timezone

from apps.billing.models import Subscription

from .models import Invoice


def invoicing_alerts(request):
    """
    Exposes has_invoicing_profile (drives the header nav link) and
    invoicing_overdue_count (badge next to it) - same shape as
    apps.vault/apps.wellness's context processors. Unlike those, Invoicing
    has no dedicated Profile model - a Subscription row existing is itself
    the "onboarded" signal (see views._ensure_subscription).
    """
    if not request.user.is_authenticated:
        return {}
    if not Subscription.objects.filter(user=request.user, product="invoicing").exists():
        return {}

    today = timezone.localdate()
    overdue = Invoice.objects.filter(
        owner=request.user, status=Invoice.Status.SENT, due_date__lt=today
    ).count()
    return {"has_invoicing_profile": True, "invoicing_overdue_count": overdue}
