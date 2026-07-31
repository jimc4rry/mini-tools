from django.utils import timezone

from .models import DailyMissionLog, WellnessProfile


def wellness_alerts(request):
    """
    Exposes has_wellness_profile (drives the header nav link) and
    wellness_missions_pending (badge next to it) - mirrors
    apps.vault.context_processors.vault_alerts's shape. Only counts *today's*
    already-assigned missions still incomplete - never creates today's
    missions here (that only happens on an actual dashboard visit), so this
    context processor stays a cheap read on every request.
    """
    if not request.user.is_authenticated:
        return {}
    if not WellnessProfile.objects.filter(user=request.user).exists():
        return {}

    today = timezone.localdate()
    pending = DailyMissionLog.objects.filter(
        user=request.user, date=today, is_completed=False
    ).count()
    return {"has_wellness_profile": True, "wellness_missions_pending": pending}
