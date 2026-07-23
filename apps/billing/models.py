from django.conf import settings
from django.db import models


class Subscription(models.Model):
    """
    Generic per-user, per-product subscription record - one Django login
    (auth.User) is shared across the whole Hub, but each app/tool has its
    own independent plan status, keyed by a `product` slug (e.g. "tracker").

    apps/tracker predates this model and keeps its own denormalized
    Business.plan_status/trial_ends_at/paddle_* fields for its existing
    UI/admin/management commands - the Paddle webhook (see webhooks.py)
    keeps those in sync for product="tracker". Any *new* paid tool should
    check this model directly instead of inventing its own plan-status
    fields.
    """

    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="billing_subscriptions"
    )
    product = models.CharField(
        max_length=50,
        help_text="Slug identifying which app/tool this subscription is for, e.g. 'tracker'.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    trial_ends_at = models.DateField(null=True, blank=True)
    paddle_subscription_id = models.CharField(max_length=100, blank=True)
    paddle_customer_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["product", "user"]

    def __str__(self):
        return f"{self.user} — {self.product} ({self.status})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @classmethod
    def is_active_for(cls, user, product):
        return cls.objects.filter(user=user, product=product, status=cls.Status.ACTIVE).exists()
