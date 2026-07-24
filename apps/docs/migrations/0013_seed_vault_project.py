from django.db import migrations

DESCRIPTION = """License & Subscription Vault is where freelancers, developers, and small teams keep track of software licenses, API keys, and SSL certificates in one place — encrypted at rest, gated behind a Master PIN, with alerts before anything expires or renews.
"""


def seed_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.update_or_create(
        slug="vault",
        defaults={
            "name": "License & Subscription Vault",
            "description": DESCRIPTION,
            "url_name": "vault:dashboard",
            "is_public": True,
            "order": 3,
        },
    )


def remove_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="vault").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0012_seed_liteqa_security_policy"),
    ]

    operations = [
        migrations.RunPython(seed_project, remove_project),
    ]
