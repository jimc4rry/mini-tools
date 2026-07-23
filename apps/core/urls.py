from django.urls import path

from . import views
from .feeds import ChangelogFeed

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("healthz", views.healthz, name="healthz"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("feed/", ChangelogFeed(), name="feed"),
]
