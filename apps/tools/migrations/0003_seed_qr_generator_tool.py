from django.db import migrations


def seed_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.update_or_create(
        slug="qr-code-generator",
        defaults={
            "name": "QR Code Generator",
            "description": "Generate a free QR code for a URL, text, phone number, email, SMS, Wi-Fi login, or contact card. No sign-up, no watermark.",
            "url_name": "qr_generator:index",
            "icon": "🔳",
            "is_active": True,
            "is_free": True,
        },
    )


def remove_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.filter(slug="qr-code-generator").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0002_toolcategory_tool_category"),
    ]

    operations = [
        migrations.RunPython(seed_tool, remove_tool),
    ]
