from django.contrib import admin

from .models import Document, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_public")
    list_filter = ("is_public",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "is_published", "updated_at")
    list_filter = ("is_published", "project")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
