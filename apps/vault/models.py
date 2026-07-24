from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .fields import EncryptedTextField

VAULT_TRIAL_LENGTH_DAYS = 14
VAULT_TRIAL_ITEM_LIMIT = 10

ALERT_THRESHOLDS_DAYS = (30, 7, 1)


class VaultProfile(models.Model):
    """
    Created once a user sets up their Master PIN (see VaultOnboardingForm) -
    its existence is what marks a platform account as "onboarded" into
    Vault, same role Business plays for Tracker.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vault_profile"
    )
    pin_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vault profile for {self.user}"


class VaultItem(models.Model):
    class ItemType(models.TextChoices):
        API_KEY = "api_key", _("API Key")
        LICENSE_KEY = "license_key", _("License Key")
        SSL_CERTIFICATE = "ssl_certificate", _("SSL Certificate")
        OTHER = "other", _("Other")

    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", _("Monthly")
        ANNUAL = "annual", _("Annual")
        LIFETIME = "lifetime", _("Lifetime")
        ONE_TIME = "one_time", _("One-time purchase")
        NONE = "none", _("No recurring cost")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vault_items"
    )
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    item_type = models.CharField(
        max_length=20, choices=ItemType.choices, default=ItemType.API_KEY, verbose_name=_("Type")
    )
    vendor = models.CharField(max_length=200, blank=True, verbose_name=_("Vendor / provider"))
    secret_value = EncryptedTextField(blank=True, verbose_name=_("Secret"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.NONE,
        verbose_name=_("Billing cycle"),
    )
    cost_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Cost")
    )
    cost_currency = models.CharField(max_length=3, default="EUR", verbose_name=_("Currency"))
    expires_at = models.DateField(null=True, blank=True, verbose_name=_("Renewal / expiry date"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expires_at", "name"]

    def __str__(self):
        return self.name

    @property
    def days_until_expiry(self):
        if not self.expires_at:
            return None
        from django.utils import timezone

        return (self.expires_at - timezone.localdate()).days

    @property
    def urgency(self):
        days = self.days_until_expiry
        if days is None:
            return "ok"
        if days < 0:
            return "expired"
        if days <= 1:
            return "critical"
        if days <= 30:
            return "warning"
        return "ok"
