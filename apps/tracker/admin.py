from django.contrib import admin

from .models import Business, Category, InventoryItem, Product


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        "name", "owner", "business_type", "plan_status", "trial_ends_at",
        "notify_days_before", "created_at",
    )
    list_filter = ("business_type", "plan_status")
    search_fields = ("name", "owner__username", "owner__email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "is_active")
    list_filter = ("business", "is_active")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "category", "unit", "unit_cost", "min_required_quantity", "is_active")
    list_filter = ("business", "category", "unit", "is_active")
    search_fields = ("name", "category__name")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("product", "business", "quantity", "expiration_date", "status", "urgency", "date_added")
    list_filter = ("business", "status")
    search_fields = ("product__name", "batch_number", "notes")
    date_hierarchy = "expiration_date"
