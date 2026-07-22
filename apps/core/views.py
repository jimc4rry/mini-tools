from django.http import HttpResponse
from django.shortcuts import render

from apps.docs.models import Document
from apps.tools.models import Tool


def home(request):
    context = {
        "documents": Document.objects.filter(is_published=True)[:6],
        "tools": Tool.objects.filter(is_active=True)[:6],
    }
    return render(request, "core/home.html", context)


def healthz(request):
    return HttpResponse("ok")
