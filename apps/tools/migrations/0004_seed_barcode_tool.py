from django.db import migrations


def seed_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.update_or_create(
        slug="barcode-validator",
        defaults={
            "name": "Barcode / EAN-13 Validator",
            "description": "Check whether a barcode's check digit is correct, or generate a valid one — EAN-8, UPC-A, and EAN-13.",
            "url_name": "barcode_tool:index",
            "icon": "🏷️",
            "is_active": True,
            "is_free": True,
            "order": 1,
        },
    )


def remove_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.filter(slug="barcode-validator").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0003_seed_qr_generator_tool"),
    ]

    operations = [
        migrations.RunPython(seed_tool, remove_tool),
    ]
