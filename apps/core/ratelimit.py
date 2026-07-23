"""
Small, dependency-free per-IP rate limiter built on Django's cache framework.

Same pattern used ad-hoc in apps/tracker/views.py (signup) and
apps/qr_generator/views.py before this was extracted — a simple counter
with a TTL, no external package needed. Fine for a single-process/single-
worker deployment (LocMemCache); if this ever runs with multiple gunicorn
workers or multiple machines, back it with a shared cache (e.g. Redis) or
the counts won't be seen across processes.
"""
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse


def _client_ip(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def is_rate_limited(request, key, max_requests, window_seconds):
    """
    Returns True (and increments) if this key/IP has already hit
    max_requests within window_seconds; otherwise records this attempt and
    returns False. Call once per incoming request you want throttled.
    """
    cache_key = f"ratelimit:{key}:{_client_ip(request)}"
    count = cache.get(cache_key, 0)
    if count >= max_requests:
        return True
    cache.set(cache_key, count + 1, window_seconds)
    return False


def ratelimit(key, max_requests, window_seconds, methods=("POST",)):
    """
    View decorator version of is_rate_limited(), for endpoints that don't
    need custom handling of the "blocked" case (unlike tracker's signup
    view, which re-renders its form with a message) — just returns a plain
    429 when the limit is hit.

    Usage:
        @ratelimit("csv_clean", max_requests=20, window_seconds=300)
        def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.method in methods and is_rate_limited(
                request, key, max_requests, window_seconds
            ):
                return HttpResponse(
                    "Too many requests from this network. Please try again in a few minutes.",
                    status=429,
                )
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
