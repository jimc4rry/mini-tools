import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Business(models.Model):
    class BusinessType(models.TextChoices):
        PHARMACY = "pharmacy", _("Pharmacy")
        MINI_MARKET = "mini_market", _("Mini Market")
        CAFE = "cafe", _("Cafe")
        DELICATESSEN = "delicatessen", _("Delicatessen")
        OTHER = "other", _("Other")

    class PlanStatus(models.TextChoices):
        TRIAL = "trial", _("Trial")
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    TRIAL_LENGTH_DAYS = 14
    TRIAL_PRODUCT_LIMIT = 50

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business"
    )
    name = models.CharField(max_length=200)
    business_type = models.CharField(
        max_length=20, choices=BusinessType.choices, default=BusinessType.OTHER
    )
    plan_status = models.CharField(
        max_length=20, choices=PlanStatus.choices, default=PlanStatus.TRIAL
    )
    trial_ends_at = models.DateField(null=True, blank=True)
    paddle_subscription_id = models.CharField(max_length=100, blank=True)
    paddle_customer_id = models.CharField(max_length=100, blank=True)
    notify_days_before = models.PositiveIntegerField(default=15)
    notify_email = models.EmailField(blank=True)
    notify_phone = models.CharField(
        max_length=20, blank=True,
        help_text=_("WhatsApp number in E.164 format, e.g. +306912345678"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "businesses"

    def __str__(self):
        return self.name

    @property
    def notification_email(self):
        return self.notify_email or self.owner.email

    @property
    def trial_days_left(self):
        if self.plan_status != self.PlanStatus.TRIAL or not self.trial_ends_at:
            return None
        return (self.trial_ends_at - timezone.localdate()).days

    @property
    def is_trial_expired(self):
        days_left = self.trial_days_left
        return days_left is not None and days_left < 0

    @property
    def product_limit_reached(self):
        if self.plan_status != self.PlanStatus.TRIAL:
            return False
        return self.products.filter(is_active=True).count() >= self.TRIAL_PRODUCT_LIMIT


# Lazy translations: evaluated to text (in the current active language) only
# when str()'d — forms.SignupForm.save() does that explicitly at signup time,
# so each business gets its default categories in whichever language was
# active when they signed up, not whatever language happened to be active
# when this module was first imported.
DEFAULT_CATEGORY_NAMES = [
    _("Food"), _("Beverages"), _("Dairy"), _("Frozen"), _("Cleaning supplies"), _("Medicine"), _("Other"),
]


class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("business", "name")
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = "piece", _("Pieces")
        KG = "kg", _("Kg")
        LITER = "liter", _("Liters")
        BOX = "box", _("Boxes")

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=64, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_required_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["business", "barcode"])]

    def __str__(self):
        return self.name

    @property
    def active_quantity(self):
        return self.inventory_items.filter(status=InventoryItem.Status.ACTIVE).aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

    @property
    def is_low_stock(self):
        if self.min_required_quantity is None:
            return False
        return self.active_quantity < self.min_required_quantity


class InventoryItem(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        CONSUMED = "consumed", _("Consumed")
        WASTED = "wasted", _("Wasted")

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="inventory_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_items"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    batch_number = models.CharField(max_length=100, blank=True)
    expiration_date = models.DateField()
    notes = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    resolved_at = models.DateTimeField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["expiration_date"]

    def __str__(self):
        return f"{self.product.name} ({self.expiration_date})"

    @property
    def days_left(self):
        return (self.expiration_date - timezone.localdate()).days

    @property
    def urgency(self):
        days = self.days_left
        if days < 0:
            return "expired"
        if days <= 7:
            return "critical"
        if days <= 15:
            return "warning"
        return "ok"

    @property
    def waste_value(self):
        if self.product.unit_cost is None:
            return None
        return self.quantity * self.product.unit_cost
