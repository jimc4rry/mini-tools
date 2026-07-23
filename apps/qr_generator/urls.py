from django.urls import path

from . import views

app_name = "qr_generator"

urlpatterns = [
    path("", views.index, name="index"),
    path("embed/", views.embed, name="embed"),
]
