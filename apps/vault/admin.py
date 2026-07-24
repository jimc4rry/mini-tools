from django.contrib import admin

from .models import VaultItem, VaultProfile


@admin.register(VaultProfile)
class VaultProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "pin_hash", "created_at")


@admin.register(VaultItem)
class VaultItemAdmin(admin.ModelAdmin):
    """
    secret_value is intentionally never shown here, in any form - the
    Master PIN reveal gate (apps/vault/views.py) is bypassed entirely by
    Django Admin, so staff/superusers browsing /admin/ must never be able
    to read a user's stored secrets through it.
    """

    list_display = ("name", "owner", "item_type", "billing_cycle", "expires_at", "is_active")
    list_filter = ("item_type", "billing_cycle", "is_active")
    search_fields = ("name", "vendor", "owner__username", "owner__email")
    date_hierarchy = "expires_at"
    exclude = ("secret_value",)
    readonly_fields = ("owner", "created_at", "updated_at")
