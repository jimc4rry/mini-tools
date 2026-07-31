from django.db import migrations

DESCRIPTION = """A calm, no-shame way to build weight-loss consistency - three small daily missions instead of calorie counting, a weekly Joker for guilt-free days, and a progress estimate based on your own real trend.

## What it does

Most weight-loss apps make you log every calorie, then guilt-trip you when you go over. Wellness does the opposite: each day it gives you 3 small, easy missions (drink water, take a short walk, eat protein at breakfast) that build consistency without the anxiety - and once a week, a "Joker" lets you eat what you want, guilt-free, on purpose.

## Key features

- **Daily missions** - 3 small, achievable tasks chosen for you each day, checked off like a simple list
- **The Grace System** - one Joker day a week to eat freely, framed as something to enjoy slowly rather than something to feel bad about
- **Real-trend prediction** - "weeks to your goal weight" calculated from your own logged weigh-ins, not a theoretical calorie deficit
- **No red, no failure states** - progress is shown in calm greens and blues, never as a warning
"""


def seed_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.update_or_create(
        slug="wellness",
        defaults={
            "name": "Wellness",
            "description": DESCRIPTION,
            "url_name": "wellness:dashboard",
            "is_public": True,
            "order": 4,
        },
    )


def remove_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="wellness").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0014_expand_vault_description"),
    ]

    operations = [
        migrations.RunPython(seed_project, remove_project),
    ]
