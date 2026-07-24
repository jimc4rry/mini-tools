from django.urls import path

from . import views

app_name = "platform_admin"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("subscriptions/<int:pk>/", views.subscription_detail, name="subscription_detail"),
    path("feedback/<int:pk>/", views.feedback_detail, name="feedback_detail"),
]
