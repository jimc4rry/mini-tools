"""
Reminder-email hook point - not implemented, since no reminder copy/schedule
was specified. Left as a stub matching this project's existing pattern:
apps.tracker's own send_expiration_notifications.py (a plain BaseCommand
using django.core.mail.send_mail), scheduled via a Railway Cron Job service
running `python manage.py send_mission_reminders` on a daily schedule -
exactly how apps.vault's check_ssl_expiry is deployed. No Celery needed for
a single daily job like this; the project doesn't run Celery/Redis anywhere.

If this ever needs to be near-real-time or fan out to many users with retries
(rather than one daily batch), Celery would replace the Cron Job service:
a `celery_app.task` wrapping the same logic below, triggered by Celery Beat
on the same schedule instead of Railway's cron, with Redis as the broker.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Emails users who haven't completed today's missions yet a gentle reminder."

    def handle(self, *args, **options):
        # Intentionally not implemented - wire up once reminder copy/timing
        # is decided. Shape it like send_expiration_notifications.py: loop
        # WellnessProfile.objects.all(), check today's DailyMissionLog
        # completion, send_mail() if any are still pending.
        self.stdout.write(self.style.WARNING("send_mission_reminders is a stub - not implemented yet."))
