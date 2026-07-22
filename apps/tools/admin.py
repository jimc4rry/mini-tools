from django.contrib import admin

from .models import Tool


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "is_free", "price_cents", "order")
    list_filter = ("is_active", "is_free")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
