from django.db import migrations


def seed_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.update_or_create(
        slug="csv-cleaner",
        defaults={
            "name": "Bulk Inventory CSV Cleaner",
            "description": "Upload a CSV, get back stray whitespace trimmed, dates normalized to YYYY-MM-DD, and exact-duplicate rows removed.",
            "url_name": "csv_cleaner:index",
            "icon": "🧹",
            "is_active": True,
            "is_free": True,
            "order": 2,
        },
    )


def remove_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.filter(slug="csv-cleaner").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0004_seed_barcode_tool"),
    ]

    operations = [
        migrations.RunPython(seed_tool, remove_tool),
    ]
