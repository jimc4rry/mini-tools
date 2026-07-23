from django.urls import path

from . import views

app_name = "og_image"

urlpatterns = [
    path("", views.generate, name="generate"),
]
