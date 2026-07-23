from django.urls import path

from . import views

app_name = "jira_helpers"

urlpatterns = [
    path("", views.index, name="index"),
]
