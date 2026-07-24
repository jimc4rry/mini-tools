from django.db import migrations

SECURITY_POLICY_BODY = """This page explains how LiteQA, a test management app for Atlassian Jira Cloud, is built and run with security in mind.

## Platform security

LiteQA has no infrastructure of its own. It runs entirely inside [Atlassian Forge](https://developer.atlassian.com/platform/forge/)'s managed, sandboxed runtime — there are no external servers, containers, or databases operated by us. Your data never leaves Atlassian's cloud, and per-site tenant isolation is enforced by the platform itself. Operating-system and network-level patching is Atlassian's responsibility, not ours.

## Access control

The app requests only the scopes it needs to function:

- `read:jira-work`
- `write:jira-work`
- `read:jira-user`
- `storage:app`
- `report:personal-data`

Admin-only actions — feature flags, the CI/CD API key — are enforced server-side against Jira's own `ADMINISTER_PROJECTS` permission. Every feature can be individually toggled per-project from the app's Settings tab.

## No password or PAT collection

LiteQA never asks for your Atlassian password, a personal access token, or any other credential. Authentication is entirely managed by Forge — the app never sees or stores your login details.

## Secret handling

The only secret the app deals with is an optional CI/CD API key, which a project admin can opt into generating. It's stored using Forge's encrypted secret storage, scoped to that project, and can be rotated or revoked at any time from the Automation tab. Treat it like a password.

## Personal data reporting

An automated daily job checks Atlassian's Personal Data Reporting API for any closed accounts among the Atlassian account IDs the app has on file, and automatically erases that data — see the [Privacy Policy](/docs/liteqa-privacy-policy/) for more.

## Reporting a vulnerability

If you find a security issue, email [jimmympo@gmail.com](mailto:jimmympo@gmail.com) with details and reproduction steps. We aim to acknowledge reports within 2 business days, and ask for reasonable time to fix an issue before it's disclosed publicly.

## Updates to this policy

The "Last updated" date above is updated whenever this policy changes materially.
"""


def seed_liteqa_security_policy(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Document = apps.get_model("docs", "Document")

    project, _ = Project.objects.get_or_create(slug="liteqa", defaults={"name": "LiteQA"})

    Document.objects.update_or_create(
        slug="liteqa-security-policy",
        defaults={
            "title": "Security Policy — LiteQA",
            "project": project,
            "summary": "How LiteQA is built and run with security in mind.",
            "body": SECURITY_POLICY_BODY,
            "is_published": True,
        },
    )


def unseed_liteqa_security_policy(apps, schema_editor):
    Document = apps.get_model("docs", "Document")
    Document.objects.filter(slug="liteqa-security-policy").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0011_seed_menuhub_project"),
    ]

    operations = [
        migrations.RunPython(seed_liteqa_security_policy, unseed_liteqa_security_policy),
    ]
