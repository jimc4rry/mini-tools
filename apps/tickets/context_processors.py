from django.db.models import Q

from apps.billing.models import Subscription

from .models import Ticket


def tickets_alerts(request):
    """
    Same shape as apps.vault/apps.wellness's context processors. Unlike
    those, "assigned to me" spans every board the user is on (owner or
    member), not a single profile - the first context processor in this
    codebase that needs an OR-based membership query rather than a plain
    owner filter.
    """
    if not request.user.is_authenticated:
        return {}
    if not Subscription.objects.filter(user=request.user, product="tickets").exists():
        return {}

    count = (
        Ticket.objects.filter(assignee=request.user)
        .exclude(status=Ticket.Status.DONE)
        .filter(Q(board__owner=request.user) | Q(board__memberships__user=request.user))
        .distinct()
        .count()
    )
    return {"has_tickets_profile": True, "tickets_assigned_count": count}
