from django.urls import path

from . import views

app_name = "csv_cleaner"

urlpatterns = [
    path("", views.index, name="index"),
]
