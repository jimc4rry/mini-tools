from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from apps.docs.models import Document, Project
from apps.tools.models import Tool


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
