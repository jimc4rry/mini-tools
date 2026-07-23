from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("created_at", "category", "name", "email", "page_path")
    list_filter = ("category",)
    search_fields = ("name", "email", "message", "page_path")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
