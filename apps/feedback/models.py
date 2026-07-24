from django.db import models
from django.utils.translation import gettext_lazy as _


class Feedback(models.Model):
    class Category(models.TextChoices):
        BUG = "bug", _("Bug report")
        FEATURE = "feature", _("Feature request")
        GENERAL = "general", _("General feedback")

    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    message = models.TextField()
    page_path = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(
        default=False,
        help_text="Set automatically when a staff member opens this submission in the admin.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.message[:50]}"
