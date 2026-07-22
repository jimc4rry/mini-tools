from django.shortcuts import get_object_or_404, render

from .models import Tool, ToolCategory


def tool_list(request):
    categories = ToolCategory.objects.all()
    tools = Tool.objects.filter(is_active=True).select_related("category")

    current_category = None
    category_slug = request.GET.get("category")
    if category_slug:
        current_category = get_object_or_404(ToolCategory, slug=category_slug)
        tools = tools.filter(category=current_category)

    context = {
        "tools": tools,
        "categories": categories,
        "current_category": current_category,
    }
    return render(request, "tools/list.html", context)
