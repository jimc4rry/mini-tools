from django.conf import settings

from apps.tools.models import Tool


def site_context(request):
    """Exposes the canonical site URL (e.g. https://minitoolshub.com) to every
    template, so canonical/og:url tags always point at the real domain even
    when the app is reached through Railway's own *.up.railway.app domain —
    without this, both domains would self-canonicalize and risk being
    indexed as duplicate content."""
    return {"site_url": settings.SITE_URL}


def current_tool_context(request):
    """
    Exposes `current_tool` when the page being rendered is a registered
    Tool's own entry view, matched by `request.resolver_match` against
    `Tool.url_name` - lets base.html record a "recently used" entry in
    localStorage without every tool app needing to know about the registry.
    """
    match = request.resolver_match
    if not match:
        return {}
    view_name = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
    tool = Tool.objects.filter(url_name=view_name, is_active=True).first()
    return {"current_tool": tool} if tool else {}
