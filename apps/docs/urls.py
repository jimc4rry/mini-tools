from django.urls import path

from . import views

app_name = "docs"

urlpatterns = [
    path("", views.document_list, name="list"),
    path("p/<slug:slug>/", views.project_detail, name="project_detail"),
    path("<slug:slug>/", views.document_detail, name="detail"),
]
