from django.db import models


class Feedback(models.Model):
    class Category(models.TextChoices):
        BUG = "bug", "Bug report"
        FEATURE = "feature", "Feature request"
        GENERAL = "general", "General feedback"

    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    message = models.TextField()
    page_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.message[:50]}"
