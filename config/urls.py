from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.docs import views as docs_views
from apps.tracker.forms import FriendlyAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("p/<slug:slug>/", docs_views.project_detail, name="project_detail"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=FriendlyAuthenticationForm,
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("apps.core.urls")),
    path("docs/", include("apps.docs.urls")),
    path("tools/", include("apps.tools.urls")),
    path("expiration-tracker/", include("apps.tracker.urls")),
]
