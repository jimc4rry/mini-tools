from django.urls import path

from . import views

app_name = "docs"

urlpatterns = [
    path("", views.document_list, name="list"),
    path("<slug:slug>/", views.document_detail, name="detail"),
]
