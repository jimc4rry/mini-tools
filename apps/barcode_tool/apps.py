from django.apps import AppConfig


class BarcodeToolConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.barcode_tool"
    label = "barcode_tool"
    verbose_name = "Barcode Validator"
