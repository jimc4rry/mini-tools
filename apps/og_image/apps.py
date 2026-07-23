from django.apps import AppConfig


class OgImageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.og_image"
    label = "og_image"
    verbose_name = "OG Image Generator"
