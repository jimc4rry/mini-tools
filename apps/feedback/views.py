from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.core.ratelimit import is_rate_limited

from .forms import FeedbackForm

RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_REQUESTS = 10


def _safe_next(request, next_path):
    if next_path and next_path.startswith("/") and not next_path.startswith("//"):
        return next_path
    return request.META.get("HTTP_REFERER") or "/"


@require_POST
def submit(request):
    next_path = _safe_next(request, request.POST.get("next"))

    if is_rate_limited(request, "feedback_submit", RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS):
        messages.error(request, _("Too many submissions from this network. Please try again in a few minutes."))
        return redirect(next_path)

    form = FeedbackForm(request.POST)

    # Honeypot tripped: silently pretend it worked, no hint given to the bot.
    if form.data.get("website"):
        return redirect(next_path)

    if not form.is_valid():
        messages.error(request, _("Couldn't send your feedback - please check the message field."))
        return redirect(next_path)

    feedback = form.save(commit=False)
    feedback.page_path = request.META.get("HTTP_REFERER", "")[:500]
    feedback.save()

    if settings.FEEDBACK_NOTIFY_EMAIL:
        send_mail(
            subject=f"[Minitools Hub] {feedback.get_category_display()}",
            message=(
                f"From: {feedback.name or 'anonymous'} <{feedback.email or 'no email'}>\n"
                f"Page: {feedback.page_path}\n\n"
                f"{feedback.message}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.FEEDBACK_NOTIFY_EMAIL],
            fail_silently=True,
        )

    messages.success(request, _("Thanks for the feedback!"))
    return redirect(next_path)
