from django.shortcuts import render

from .models import Tool


def tool_list(request):
    tools = Tool.objects.filter(is_active=True)
    return render(request, "tools/list.html", {"tools": tools})
