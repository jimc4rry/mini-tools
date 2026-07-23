from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from apps.core.ratelimit import is_rate_limited
from apps.docs.models import Document, Project
from apps.tools.models import Tool

SEARCH_RATE_LIMIT_MAX_REQUESTS = 60
SEARCH_RATE_LIMIT_WINDOW_SECONDS = 60
SEARCH_MIN_QUERY_LENGTH = 2
SEARCH_MAX_RESULTS_PER_TYPE = 5


def home(request):
    context = {
        "tools": Tool.objects.filter(is_active=True)[:6],
        "all_projects": Project.objects.filter(is_public=True),
        "current_project": None,
    }
    return render(request, "core/home.html", context)


def healthz(request):
    return HttpResponse("ok")


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /expiration-tracker/",
        f"Sitemap: {settings.SITE_URL}{reverse('core:sitemap_xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def search_json(request):
    """
    Backs the Ctrl+K command palette (see templates/base.html). Plain
    icontains matching - the catalog is small enough that a real search
    engine (Postgres full-text, Elasticsearch, etc.) would be overkill.
    """
    query = (request.GET.get("q") or "").strip()
    if len(query) < SEARCH_MIN_QUERY_LENGTH:
        return JsonResponse({"results": []})

    if is_rate_limited(request, "search", SEARCH_RATE_LIMIT_MAX_REQUESTS, SEARCH_RATE_LIMIT_WINDOW_SECONDS):
        return JsonResponse({"results": []}, status=429)

    results = []

    tools = Tool.objects.filter(is_active=True).filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:SEARCH_MAX_RESULTS_PER_TYPE]
    for tool in tools:
        results.append({
            "type": "Tool",
            "title": tool.name,
            "description": tool.description[:120],
            "url": tool.get_absolute_url(),
        })

    documents = Document.objects.filter(is_published=True).filter(
        Q(title__icontains=query) | Q(summary__icontains=query)
    )[:SEARCH_MAX_RESULTS_PER_TYPE]
    for document in documents:
        results.append({
            "type": "Document",
            "title": document.title,
            "description": document.summary[:120],
            "url": document.get_absolute_url(),
        })

    projects = Project.objects.filter(is_public=True).filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:SEARCH_MAX_RESULTS_PER_TYPE]
    for project in projects:
        results.append({
            "type": "Application",
            "title": project.name,
            "description": project.description[:120],
            "url": project.get_absolute_url(),
        })

    return JsonResponse({"results": results})


def sitemap_xml(request):
    """
    Hand-rolled rather than django.contrib.sitemaps: this site's set of public
    URLs is small and heterogeneous (a handful of static pages, published
    Documents, public Projects), so a plain list is simpler than wiring up
    Sitemap classes for it.
    """
    paths = [
        reverse("core:home"),
        reverse("docs:list"),
        reverse("tools:list"),
        reverse("qr_generator:index"),
    ]
    for project in Project.objects.filter(is_public=True):
        paths.append(project.get_absolute_url())
    for document in Document.objects.filter(is_published=True):
        paths.append(document.get_absolute_url())

    entries = "\n".join(f"  <url><loc>{settings.SITE_URL}{path}</loc></url>" for path in paths)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>"
    )
    return HttpResponse(xml, content_type="application/xml")
