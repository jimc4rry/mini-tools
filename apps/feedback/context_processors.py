from .models import Feedback


def unread_badge(request):
    """
    Exposes `unread_feedback_count` for the Django admin sidebar badge (see
    templates/admin/app_list.html). Scoped to /admin/ staff requests only -
    this would be a wasted query on every public page otherwise.
    """
    if not request.path.startswith("/admin/"):
        return {}
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    return {"unread_feedback_count": Feedback.objects.filter(is_read=False).count()}
