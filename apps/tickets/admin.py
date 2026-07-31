from django.contrib import admin

from .models import Board, BoardMembership, Comment, Tag, Ticket


class BoardMembershipInline(admin.TabularInline):
    model = BoardMembership
    extra = 0


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__username")
    inlines = [BoardMembershipInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "board", "color")
    list_filter = ("board",)
    search_fields = ("name",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("title", "board", "status", "priority", "due_date", "assignee", "reporter")
    list_filter = ("status", "priority")
    search_fields = ("title", "board__name")
    date_hierarchy = "due_date"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("ticket__title", "author__username")
