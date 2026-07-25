from django.db import migrations

DESCRIPTION = """Keep every API key, software license, and SSL certificate your business depends on in one encrypted place, with automatic alerts before anything expires.

## What it does

Freelancers, developers, and small teams typically track their API keys, license keys, and renewal dates across notes apps, spreadsheets, and sticky notes - which is exactly how renewals get missed and keys leak. Vault replaces that with a single dashboard: add an item once, and it stays encrypted, organized, and monitored from then on.

## Who it's for

- **Developers** juggling API keys across dozens of third-party services (payment providers, email, hosting, SaaS tools)
- **Freelancers and agencies** managing software licenses and subscriptions for multiple clients
- **Small business owners** who need to know before a domain, SSL certificate, or paid tool renews or lapses

## Key features

- **Encrypted storage** - every secret value is encrypted at rest, never stored in plain text
- **Master PIN reveal gate** - secrets stay masked on screen; a PIN is required before anything is shown or copied, rate-limited against brute-force attempts
- **Expiration alerts** - a dashboard "Alerts" section and a header badge surface anything expiring within 30 days, so nothing slips through
- **Automatic SSL certificate checking** - point an item at a real domain and Vault checks its live TLS certificate daily, keeping the expiry date accurate without manual upkeep
- **Cost tracking** - monthly and annual recurring cost totals across every subscription, computed automatically from each item's billing cycle
- **One login for the whole Hub** - the same account used across every Minitools Hub app, no separate signup

## Supported item types

API keys, software license keys, SSL certificates, and any other credential or subscription worth tracking - each with its own vendor, cost, billing cycle, and renewal date.
"""


def update_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="vault").update(description=DESCRIPTION)


def revert_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="vault").update(
        description=(
            "License & Subscription Vault is where freelancers, developers, and small teams "
            "keep track of software licenses, API keys, and SSL certificates in one place - "
            "encrypted at rest, gated behind a Master PIN, with alerts before anything expires "
            "or renews.\n"
        )
    )


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0013_seed_vault_project"),
    ]

    operations = [
        migrations.RunPython(update_project, revert_project),
    ]
