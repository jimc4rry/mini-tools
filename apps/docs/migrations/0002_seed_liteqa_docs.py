from django.db import migrations

PRIVACY_BODY = """LiteQA is a test management app for Atlassian Jira Cloud. This page explains what data the app touches, why, and where it lives.

**In short:** everything the app stores lives inside your own Jira site's Atlassian Forge storage. We don't run our own servers, we don't see your data, and we don't sell or share it with anyone.

## What we collect

When you and your team use LiteQA inside a Jira work item, the app stores the content you create with it:

| Data | Why we store it |
|---|---|
| Test case titles, steps, scenarios, and "business need" notes | The core content of your test suite |
| Execution results and history (pass / fail / blocked, comments, timestamps, duration) | So your team can see what was tested, when, and by whom |
| Atlassian account ID of whoever ran a test | Attribution for the execution history — resolved to a display name via Jira's own user API |
| Folder names and CI/CD webhook API keys, if you use those optional features | Organizing test tickets, and authenticating automated result submissions from your pipeline |
| A name and comment, only if someone opens a report you've explicitly shared and submits a sign-off | Attributing that approval on a report you chose to make public |

## What we don't collect

- No analytics or usage tracking beyond Atlassian's own platform-level app metrics
- No advertising identifiers, cookies, or third-party trackers
- No payment or financial information (the app has no in-app purchases)
- No data from outside the Jira site where the app is installed

## Where it's stored

All app data is stored using [Atlassian Forge Storage](https://developer.atlassian.com/platform/forge/storage-reference/), a managed data layer that runs entirely on Atlassian's own cloud infrastructure. We don't operate any servers of our own, and no app data is copied to a third-party host. Storage is isolated per Jira site — one customer's data is never visible to another.

## How it's used

Data is used only to render the app's own features back to your team: the test case panels, traceability view, reports, dashboard gadget, and the optional CI webhook and shareable-report links you turn on yourself. Nothing is used for any purpose beyond operating the app as described in its listing.

## Sharing

We do not sell, rent, or share your data with third parties. The only data that becomes visible outside your Jira site is what you deliberately choose to expose:

- If you generate a **shareable report link**, anyone with that link can view the report — that's the intended purpose of the feature, and it can be turned off entirely from the app's Settings tab.
- If you enable the **CI/CD webhook**, whoever holds the API key you generate can submit test results — treat that key like a password.

## Retention & deletion

Data is retained for as long as the app remains installed on your Jira site. Uninstalling the app removes its stored data. If you need data removed sooner — for example, a single test plan or a sign-off entry — contact us at the address below.

We also run an automated daily check against Atlassian's Personal Data Reporting API for every Atlassian account ID we have on file (the person who executed a test). If Atlassian reports that an account has been closed, we erase that account's ID from our records automatically, without you needing to ask.

## Your rights

Depending on your location, you may have rights to access, correct, export, or delete your data. Because all app data lives in your own Jira site's storage, your Jira site administrator already has direct access to it through the app itself. For anything the app's own UI doesn't let you do directly, email us and we'll help.

## Children's privacy

LiteQA is a business tool distributed through the Atlassian Marketplace and is not directed at, or knowingly used by, children.

## Changes to this policy

If this policy changes, we'll update the "Last updated" date above. Material changes will be noted in the app's listing changelog.

## Contact

Questions about this policy or a data request: [jimmympo@gmail.com](mailto:jimmympo@gmail.com)
"""

TERMS_BODY = """These terms cover your use of LiteQA, a test management app for Atlassian Jira Cloud. By installing or using the app, you agree to them.

**Plain-language summary:** use the app to manage your tests, don't abuse it or try to break it, we provide it as-is without uptime guarantees beyond Atlassian's own platform, and either side can walk away at any time by uninstalling.

## 1. Acceptance

By installing, accessing, or using LiteQA ("the app"), you agree to these Terms of Service on behalf of yourself and, if applicable, the organization that installed the app. If you don't agree, don't install or use the app.

## 2. The service

LiteQA is an Atlassian Forge application that adds test case management, execution tracking, traceability, reporting, and related features to Jira Cloud. It runs entirely within Atlassian's Forge platform and is subject to Atlassian's own Cloud Terms in addition to these terms.

## 3. License

We grant you a limited, non-exclusive, non-transferable, revocable license to install and use the app for as long as it remains listed and your installation is active, solely for your internal business purposes within your own Jira site.

## 4. Acceptable use

You agree not to:

- Reverse engineer, decompile, or attempt to extract the app's source code beyond what Atlassian's platform inherently exposes
- Use the app to store or transmit unlawful content, or to violate a third party's rights
- Attempt to bypass, probe, or disrupt the app's access controls (including the CI/CD webhook or shareable-report features) in a way not intended by their design
- Resell, sublicense, or white-label the app without our written permission

## 5. Your content

You retain all rights to the test cases, execution results, and other content you create using the app. We claim no ownership over it. See our Privacy Policy for how that content is stored and handled.

## 6. Availability

We aim to keep the app working reliably, but we don't guarantee uninterrupted availability. Because the app runs on Atlassian's Forge infrastructure, its uptime is also subject to Atlassian's own platform availability, which is outside our control.

## 7. Warranty disclaimer

The app is provided "as is" and "as available," without warranties of any kind, express or implied, including — to the extent permitted by law — implied warranties of merchantability, fitness for a particular purpose, and non-infringement.

## 8. Limitation of liability

To the maximum extent permitted by law, we are not liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of data, revenue, or business opportunity arising from your use of the app.

## 9. Term & termination

These terms apply for as long as you use the app. You may stop at any time by uninstalling it from your Jira site. We may suspend or terminate access for a specific installation if we reasonably believe these terms are being violated.

## 10. Changes to these terms

We may update these terms as the app evolves. We'll update the "Last updated" date above; continued use after a change means you accept the revised terms.

## 11. Governing law

These terms are governed by the laws of Greece, without regard to conflict-of-law principles, unless otherwise required by the mandatory law of your own jurisdiction.

## 12. Contact

Questions about these terms: [jimmympo@gmail.com](mailto:jimmympo@gmail.com)
"""

SUPPORT_BODY = """Stuck, found a bug, or want to request a feature? Here's how to reach us and what to include.

**Email support** — We read every message ourselves. Typical response time is within **2 business days**. [Email jimmympo@gmail.com](mailto:jimmympo@gmail.com)

**Before you write** — Check that your Jira project has the **Test** issue type and **Tests** link type set up — the app's Setup banner on the Test Management page will tell you if either is missing.

## Reporting a bug

The faster we can reproduce it, the faster we can fix it. Please include:

1. The Jira issue key you were working on (e.g. `SCRUM-5`)
2. What you expected to happen, and what happened instead
3. A screenshot, if the issue is visual
4. Whether it happens every time or only sometimes

## Requesting a feature

Tell us the problem you're trying to solve, not just the feature you have in mind — sometimes there's already a faster path to it. We read every request, though we can't promise a timeline.

## Status & known limitations

| Status | Details |
|---|---|
| Supported | Manual + automated test cases, execution history, traceability, reports, CI/CD webhook, shareable sign-off reports |
| By design | Each Jira site's data is isolated — there's no cross-site or cross-org reporting |
| Not yet | AI-generated test cases and native Confluence embedding are on the roadmap, not shipped yet |

## Contact

[jimmympo@gmail.com](mailto:jimmympo@gmail.com)
"""


def seed_liteqa_docs(apps, schema_editor):
    Category = apps.get_model("docs", "Category")
    Document = apps.get_model("docs", "Document")

    category, _ = Category.objects.get_or_create(
        slug="liteqa", defaults={"name": "LiteQA"}
    )

    docs = [
        (
            "liteqa-privacy-policy",
            "Privacy Policy — LiteQA",
            "Privacy policy for the LiteQA Jira Cloud app.",
            PRIVACY_BODY,
        ),
        (
            "liteqa-terms-of-service",
            "Terms of Service — LiteQA",
            "Terms of service for the LiteQA Jira Cloud app.",
            TERMS_BODY,
        ),
        (
            "liteqa-support",
            "Support — LiteQA",
            "How to get support for the LiteQA Jira Cloud app.",
            SUPPORT_BODY,
        ),
    ]

    for slug, title, summary, body in docs:
        Document.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "category": category,
                "summary": summary,
                "body": body,
                "is_published": True,
            },
        )


def unseed_liteqa_docs(apps, schema_editor):
    Document = apps.get_model("docs", "Document")
    Document.objects.filter(
        slug__in=["liteqa-privacy-policy", "liteqa-terms-of-service", "liteqa-support"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_liteqa_docs, unseed_liteqa_docs),
    ]
