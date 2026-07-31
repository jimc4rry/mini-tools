from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

INVOICING_TRIAL_LENGTH_DAYS = 14


class Client(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoicing_clients"
    )
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=50, blank=True, verbose_name=_("Phone"))
    address = models.TextField(blank=True, verbose_name=_("Address"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Invoice(models.Model):
    class Kind(models.TextChoices):
        QUOTE = "quote", _("Quote")
        INVOICE = "invoice", _("Invoice")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SENT = "sent", _("Sent")
        PAID = "paid", _("Paid")
        CANCELLED = "cancelled", _("Cancelled")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name="invoices", verbose_name=_("Client")
    )
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.INVOICE)
    number = models.CharField(max_length=30, verbose_name=_("Number"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField(verbose_name=_("Issue date"))
    due_date = models.DateField(verbose_name=_("Due date"))
    currency = models.CharField(max_length=3, default="EUR", verbose_name=_("Currency"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("owner", "kind", "number")
        ordering = ["-issue_date", "-id"]

    def __str__(self):
        return f"{self.number} - {self.client}"

    @property
    def total(self):
        raw = sum((item.line_total for item in self.items.all()), Decimal("0"))
        return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def is_overdue(self):
        return self.status == self.Status.SENT and self.due_date < timezone.localdate()

    @property
    def display_status(self):
        """The Status choice, except Sent-but-past-due shows as Overdue without a separate DB state."""
        return "overdue" if self.is_overdue else self.status

    @classmethod
    def next_number(cls, owner, kind):
        prefix = "QUO" if kind == cls.Kind.QUOTE else "INV"
        count = cls.objects.filter(owner=owner, kind=kind).count()
        return f"{prefix}-{count + 1:04d}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=300, verbose_name=_("Description"))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_("Qty"))
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Unit price")
    )

    @property
    def line_total(self):
        return (self.quantity * self.unit_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def __str__(self):
        return self.description
