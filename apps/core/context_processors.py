from django.conf import settings


def site_context(request):
    """Exposes the canonical site URL (e.g. https://minitoolshub.com) to every
    template, so canonical/og:url tags always point at the real domain even
    when the app is reached through Railway's own *.up.railway.app domain —
    without this, both domains would self-canonicalize and risk being
    indexed as duplicate content."""
    return {"site_url": settings.SITE_URL}
