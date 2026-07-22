from django.urls import path

from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tool_list, name="list"),
]
