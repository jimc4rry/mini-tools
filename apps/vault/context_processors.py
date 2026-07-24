import datetime

from django.utils import timezone

from .models import VaultItem, VaultProfile


def vault_alerts(request):
    """
    Exposes has_vault_profile (drives the header nav link) and
    vault_expiring_soon_count (badge next to it) - mirrors
    apps.feedback.context_processors.unread_badge's shape, but scoped to
    any onboarded user rather than superusers only, since this is a
    per-user alert, not an admin stat.
    """
    if not request.user.is_authenticated:
        return {}
    if not VaultProfile.objects.filter(user=request.user).exists():
        return {}

    cutoff = timezone.localdate() + datetime.timedelta(days=30)
    count = VaultItem.objects.filter(
        owner=request.user, is_active=True, expires_at__isnull=False, expires_at__lte=cutoff
    ).count()
    return {"has_vault_profile": True, "vault_expiring_soon_count": count}
