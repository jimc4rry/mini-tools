"""
Sends each business a WhatsApp digest of inventory items nearing expiration, via Twilio.

Setup (needs your own Twilio account — this is scaffolding, not wired to a live account):
1. Create a Twilio account and enable WhatsApp (Twilio Console -> Messaging -> Try WhatsApp,
   or apply for a verified WhatsApp Business sender for production use).
2. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM in .env
   (TWILIO_WHATSAPP_FROM looks like "whatsapp:+14155238886" for the sandbox number).
3. Each business fills in its WhatsApp number under Ρυθμίσεις (Business.notify_phone,
   E.164 format e.g. +306912345678).
4. Twilio's Sandbox only delivers to numbers that have joined the sandbox (send the join
   code to the sandbox number from WhatsApp first). Production sending outside a 24h
   customer-service window requires a pre-approved WhatsApp message template — swap the
   plain `body=` call below for `content_sid=` once you have one approved.

Until the three TWILIO_* settings are configured, this command exits without sending
anything (safe no-op), so it can be scheduled alongside send_expiration_notifications
without crashing on machines that haven't set up Twilio yet.
"""
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tracker.models import Business, InventoryItem


class Command(BaseCommand):
    help = "Sends each business a WhatsApp digest (via Twilio) of inventory items nearing expiration."

    def handle(self, *args, **options):
        account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        whatsapp_from = getattr(settings, "TWILIO_WHATSAPP_FROM", "")

        if not (account_sid and auth_token and whatsapp_from):
            self.stdout.write(self.style.WARNING(
                "Twilio δεν έχει ρυθμιστεί (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/"
                "TWILIO_WHATSAPP_FROM) — παραλείπεται."
            ))
            return

        from twilio.rest import Client  # imported lazily so the package is optional until configured

        client = Client(account_sid, auth_token)
        today = timezone.localdate()
        sent_count = 0

        for business in Business.objects.exclude(plan_status=Business.PlanStatus.INACTIVE):
            if not business.notify_phone:
                continue

            cutoff = today + datetime.timedelta(days=business.notify_days_before)
            items = (
                business.inventory_items.select_related("product")
                .filter(status=InventoryItem.Status.ACTIVE, expiration_date__lte=cutoff)
                .order_by("expiration_date")
            )
            if not items:
                continue

            lines = [f"📦 {business.name}: {items.count()} προϊόντα λήγουν σύντομα:"]
            for item in items[:10]:
                days_left = (item.expiration_date - today).days
                status = "ΛΗΓΜΕΝΟ" if days_left < 0 else f"{days_left}μ"
                lines.append(f"- {item.product.name} ({status})")
            if items.count() > 10:
                lines.append(f"...και {items.count() - 10} ακόμα.")

            try:
                client.messages.create(
                    from_=whatsapp_from,
                    to=f"whatsapp:{business.notify_phone}",
                    body="\n".join(lines),
                )
            except Exception as exc:  # noqa: BLE001 — surface any Twilio API error per business, keep looping
                self.stdout.write(self.style.ERROR(f"Failed for {business.name}: {exc}"))
                continue

            sent_count += 1
            self.stdout.write(self.style.SUCCESS(f"Notified {business.name} ({business.notify_phone})"))

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {sent_count} WhatsApp notification(s)."))
