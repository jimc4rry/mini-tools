from django.urls import path

from . import views, webhooks

app_name = "billing"

urlpatterns = [
    path("webhook/", webhooks.paddle_webhook, name="paddle_webhook"),
    path("upgrade/<str:product>/", views.upgrade, name="upgrade"),
]
