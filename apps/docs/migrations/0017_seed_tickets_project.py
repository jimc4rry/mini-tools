from django.db import migrations

DESCRIPTION = """A Jira-lite ticketing system for small teams - boards, drag-and-drop Kanban columns, comments, and assignment, without the setup overhead of a full project management suite.

## What it does

Small teams often reach for a full Jira/Linear setup just to track a handful of tasks between two or three people. Tickets keeps it simple: create a board, invite the people working on it with you, and drag tickets between To Do, In Progress, and Done as work happens.

## Key features

- **Boards with invited members** - the first shared, multi-user workspace on the Hub. Invite an existing account by username and they see the board too
- **Drag-and-drop Kanban** - move tickets between columns directly, no extra clicks
- **Comments & assignment** - every ticket has a comment thread and can be assigned to anyone on the board
- **A header badge** - shows how many open tickets are assigned to you, across every board you're on
"""


def seed_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.update_or_create(
        slug="tickets",
        defaults={
            "name": "Tickets",
            "description": DESCRIPTION,
            "url_name": "tickets:board_list",
            "is_public": True,
            "order": 6,
        },
    )


def remove_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="tickets").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0016_seed_invoicing_project"),
    ]

    operations = [
        migrations.RunPython(seed_project, remove_project),
    ]
