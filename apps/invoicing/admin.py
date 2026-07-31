from django.contrib import admin

from .models import Client, Invoice, InvoiceItem


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "email", "created_at")
    search_fields = ("name", "email", "owner__username")


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "owner", "client", "kind", "status", "issue_date", "due_date")
    list_filter = ("kind", "status")
    search_fields = ("number", "client__name", "owner__username")
    inlines = [InvoiceItemInline]
