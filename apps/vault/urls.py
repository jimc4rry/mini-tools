from django.urls import path

from . import views

app_name = "vault"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("start/", views.start_trial, name="start_trial"),
    path("items/new/", views.item_create, name="item_create"),
    path("items/<int:pk>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:pk>/delete/", views.item_delete, name="item_delete"),
    path("items/<int:pk>/reveal/", views.reveal_item, name="reveal_item"),
    path("unlock/", views.unlock, name="unlock"),
    path("settings/", views.settings_view, name="settings"),
]
