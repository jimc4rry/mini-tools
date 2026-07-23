from django.db import migrations


def seed_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.update_or_create(
        slug="jira-helpers",
        defaults={
            "name": "Jira Smart Commit & Branch Name Generator",
            "description": "Generate Git branch names, Jira smart-commit syntax, and Gherkin/BDD scenario skeletons.",
            "url_name": "jira_helpers:index",
            "icon": "🔀",
            "is_active": True,
            "is_free": True,
            "order": 3,
        },
    )


def remove_tool(apps, schema_editor):
    Tool = apps.get_model("tools", "Tool")
    Tool.objects.filter(slug="jira-helpers").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0005_seed_csv_cleaner_tool"),
    ]

    operations = [
        migrations.RunPython(seed_tool, remove_tool),
    ]
