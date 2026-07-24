from .models import Feedback


def unread_badge(request):
    """
    Exposes `unread_feedback_count` for the Django admin sidebar badge (see
    templates/admin/app_list.html) and the "Platform Admin" header link
    badge (see templates/base.html). Scoped to superusers only - the extra
    query only ever runs for the site operator's own logged-in session,
    never for public visitors.
    """
    if not request.user.is_authenticated or not request.user.is_superuser:
        return {}
    return {"unread_feedback_count": Feedback.objects.filter(is_read=False).count()}
