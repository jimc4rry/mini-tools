from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.shortcuts import redirect

from apps.core.ratelimit import is_rate_limited

from .forms import SubscribeForm
from .models import Subscriber

RATE_LIMIT_WINDOW_SECONDS = 300
RATE_LIMIT_MAX_REQUESTS = 10


def _safe_next(request, next_path):
    if next_path and next_path.startswith("/") and not next_path.startswith("//"):
        return next_path
    return request.META.get("HTTP_REFERER") or "/"


@require_POST
def subscribe(request):
    next_path = _safe_next(request, request.POST.get("next"))

    if is_rate_limited(request, "newsletter_subscribe", RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS):
        messages.error(request, _("Too many attempts from this network. Please try again in a few minutes."))
        return redirect(next_path)

    form = SubscribeForm(request.POST)

    # Honeypot tripped: silently pretend it worked, no hint given to the bot.
    if form.data.get("website"):
        return redirect(next_path)

    if not form.is_valid():
        messages.error(request, _("Enter a valid email address."))
        return redirect(next_path)

    # get_or_create rather than surfacing "already subscribed" - no reason to
    # let a public form confirm which emails are already on the list.
    email = form.cleaned_data["email"]
    Subscriber.objects.get_or_create(email=email)

    messages.success(request, _("Subscribed! We'll email you when new free tools launch."))
    return redirect(next_path)
