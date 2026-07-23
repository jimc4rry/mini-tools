from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "status", "trial_ends_at", "updated_at")
    list_filter = ("product", "status")
    search_fields = ("user__username", "user__email", "paddle_subscription_id", "paddle_customer_id")
