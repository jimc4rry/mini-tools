from django.db import migrations

DESCRIPTION = """Expiration Date and Inventory Tracker is a lightweight inventory app for small businesses (pharmacies, mini markets, cafes, delis) to track product batches, expiration dates, and waste — with barcode scanning, low-stock alerts, and email/WhatsApp expiration digests.
"""


def seed_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.update_or_create(
        slug="expiration-tracker",
        defaults={
            "name": "Expiration Date and Inventory Tracker",
            "description": DESCRIPTION,
            "url_name": "dashboard",
            "is_public": True,
            "order": 1,
        },
    )


def remove_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="expiration-tracker").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0007_alter_project_options_project_order_project_url_name"),
    ]

    operations = [
        migrations.RunPython(seed_project, remove_project),
    ]
