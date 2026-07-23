from django.apps import AppConfig


class CsvCleanerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.csv_cleaner"
    label = "csv_cleaner"
    verbose_name = "CSV Cleaner"
