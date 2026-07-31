from django.urls import path

from . import views

app_name = "wellness"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("start/", views.start_trial, name="start_trial"),
    path("log-weight/", views.log_weight, name="log_weight"),
    path("missions/<int:pk>/toggle/", views.toggle_mission, name="toggle_mission"),
    path("grace-day/", views.use_grace_day, name="use_grace_day"),
    path("settings/", views.settings_view, name="settings"),
]
