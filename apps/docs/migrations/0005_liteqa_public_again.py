from django.db import migrations


def show_liteqa(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="liteqa").update(is_public=True)


def hide_liteqa(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="liteqa").update(is_public=False)


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0004_project_is_public"),
    ]

    operations = [
        migrations.RunPython(show_liteqa, hide_liteqa),
    ]
