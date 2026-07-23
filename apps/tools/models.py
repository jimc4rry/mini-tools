from django.db import models
from django.urls import NoReverseMatch, reverse


class ToolCategory(models.Model):
    """A category shown in the left sidebar of the tools marketplace page."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Optional emoji shown next to the name.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "tool categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("tools:list") + f"?category={self.slug}"


class Tool(models.Model):
    """
    Registry entry for a mini-tool listed on the marketplace landing page.

    Each real tool is implemented as its own Django app (own models/views/
    templates) and registers itself here so it shows up in the catalog.
    Pricing fields are in place for the future billing integration
    (Stripe checkout + webhook) — until that's wired up, treat every tool
    as free regardless of these fields.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        ToolCategory, on_delete=models.PROTECT, related_name="tools", null=True, blank=True
    )
    description = models.TextField(blank=True)
    url_name = models.CharField(
        max_length=200,
        help_text="Named URL of the tool's entry view, e.g. 'qr_generator:index'.",
    )
    icon = models.CharField(max_length=10, blank=True, help_text="Optional emoji, e.g. \U0001F527.")
    is_active = models.BooleanField(default=True)
    is_free = models.BooleanField(default=True)
    price_cents = models.PositiveIntegerField(
        default=0, help_text="Price in cents if not free. Billing integration pending."
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return ""
