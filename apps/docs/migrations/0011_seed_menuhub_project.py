from django.db import migrations

DESCRIPTION = """MenuHub is a digital QR code menu platform for restaurants, cafes, and bars — create a QR code menu in minutes, update prices instantly with no reprinting, and take orders straight from the table. Hosted separately at [getmenuhub.com](https://getmenuhub.com/).
"""


def seed_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.update_or_create(
        slug="menuhub",
        defaults={
            "name": "MenuHub",
            "description": DESCRIPTION,
            "external_url": "https://getmenuhub.com/",
            "is_public": True,
            "order": 2,
        },
    )


def remove_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="menuhub").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0010_project_external_url_alter_project_url_name"),
    ]

    operations = [
        migrations.RunPython(seed_project, remove_project),
    ]
