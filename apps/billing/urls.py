from django.urls import path

from . import webhooks

app_name = "billing"

urlpatterns = [
    path("webhook/", webhooks.paddle_webhook, name="paddle_webhook"),
]
