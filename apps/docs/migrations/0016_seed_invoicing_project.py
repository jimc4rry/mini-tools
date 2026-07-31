from django.db import migrations

DESCRIPTION = """Create professional invoices and quotes for your clients in minutes, track who's paid and who's overdue, and print or save straight to PDF - no spreadsheet templates or separate invoicing software needed.

## What it does

Freelancers and small businesses often juggle invoicing between spreadsheet templates, a separate paid tool, and manual reminders about who still owes them money. Invoicing keeps clients, invoices, and quotes in one place on the Hub you already use.

## Key features

- **Clients & line items** - build an invoice or quote from simple line items (description, quantity, unit price), automatically totalled
- **Auto numbering** - invoices and quotes are numbered sequentially per type (INV-0001, QUO-0001) so nothing collides
- **Status tracking** - Draft, Sent, Paid, or Cancelled, with overdue invoices flagged automatically once the due date passes
- **Print or save as PDF** - a clean, print-ready invoice page, no extra software or export step needed
- **A header badge for overdue invoices** - so a late payment never gets forgotten
"""


def seed_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.update_or_create(
        slug="invoicing",
        defaults={
            "name": "Invoicing",
            "description": DESCRIPTION,
            "url_name": "invoicing:dashboard",
            "is_public": True,
            "order": 5,
        },
    )


def remove_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="invoicing").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0015_seed_wellness_project"),
    ]

    operations = [
        migrations.RunPython(seed_project, remove_project),
    ]
