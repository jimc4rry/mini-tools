from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("created_at", "is_read", "category", "name", "email", "page_path")
    list_filter = ("is_read", "category")
    search_fields = ("name", "email", "message", "page_path")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Opening a submission is what "reading" it means here - no separate
        # mark-as-read action needed.
        Feedback.objects.filter(pk=object_id, is_read=False).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)
