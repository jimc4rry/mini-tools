from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("docs/", include("apps.docs.urls")),
    path("tools/", include("apps.tools.urls")),
]
