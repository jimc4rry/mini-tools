from django.contrib import admin

from .models import Tool, ToolCategory


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "is_free", "price_cents", "order")
    list_filter = ("is_active", "is_free", "category")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
