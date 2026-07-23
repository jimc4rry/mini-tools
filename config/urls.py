from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.core import views as core_views
from apps.docs import views as docs_views
from apps.tracker.forms import FriendlyAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("p/<slug:slug>/", docs_views.project_detail, name="project_detail"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=FriendlyAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/signup/", core_views.signup, name="signup"),
    path("", include("apps.core.urls")),
    path("docs/", include("apps.docs.urls")),
    path("tools/", include("apps.tools.urls")),
    path("expiration-tracker/", include("apps.tracker.urls")),
    path("qr-code-generator/", include("apps.qr_generator.urls")),
    path("barcode-validator/", include("apps.barcode_tool.urls")),
    path("csv-cleaner/", include("apps.csv_cleaner.urls")),
    path("jira-helpers/", include("apps.jira_helpers.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("og-image/", include("apps.og_image.urls")),
    path("newsletter/", include("apps.newsletter.urls")),
    path("billing/", include("apps.billing.urls")),
    path("platform-admin/", include("apps.platform_admin.urls")),
]
