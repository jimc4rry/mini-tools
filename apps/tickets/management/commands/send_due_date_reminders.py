"""
Emails each assigned ticket's assignee one day before its due_date.

Scheduled the same way as apps.vault's check_ssl_expiry: a second Railway
service pointed at this repo, with its own Cron Schedule and Custom Start
Command (`python manage.py send_due_date_reminders`) set in that service's
Settings tab, running once a day.

Bilingual note: nothing in this project stores a per-user language
preference (the EN/EL switcher is a browser cookie, set client-side, not a
User field) - so there is no reliable way for a backend command to know
which language a given assignee prefers. Rather than guess (and risk
emailing someone in a language they don't read), each reminder includes
both an English and a Greek section in the same message, using
`django.utils.translation.activate()` to render each section's `gettext()`
calls in that language.
"""
import datetime

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from apps.tickets.models import Ticket


def _render_section(language, ticket):
    with translation.override(language):
        lines = [
            _("Reminder: \"%(title)s\" is due tomorrow (%(due_date)s).")
            % {"title": ticket.title, "due_date": ticket.due_date.strftime("%d/%m/%Y")},
            _("Board: %(board)s") % {"board": ticket.board.name},
        ]
        return "\n".join(lines)


class Command(BaseCommand):
    help = "Emails each ticket's assignee a reminder the day before its due_date."

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        tickets = (
            Ticket.objects.filter(due_date=tomorrow)
            .exclude(status=Ticket.Status.DONE)
            .exclude(assignee__isnull=True)
            .select_related("assignee", "board")
        )

        sent_count = 0
        for ticket in tickets:
            to_email = ticket.assignee.email
            if not to_email:
                self.stdout.write(
                    self.style.WARNING(f"Skipping ticket {ticket.pk}: assignee has no email on file")
                )
                continue

            body = "\n\n".join(
                [_render_section("en", ticket), _render_section("el", ticket)]
            )
            send_mail(
                subject=f"[Tickets] {ticket.title} - due tomorrow",
                message=body,
                from_email=None,
                recipient_list=[to_email],
            )
            sent_count += 1
            self.stdout.write(self.style.SUCCESS(f"Reminded {ticket.assignee} about ticket {ticket.pk}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {sent_count} reminder(s)."))
