import datetime

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tracker.models import Business, InventoryItem


class Command(BaseCommand):
    help = "Sends each business an email digest of inventory items nearing expiration."

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent_count = 0

        for business in Business.objects.exclude(plan_status=Business.PlanStatus.INACTIVE):
            cutoff = today + datetime.timedelta(days=business.notify_days_before)
            items = (
                business.inventory_items.select_related("product")
                .filter(status=InventoryItem.Status.ACTIVE, expiration_date__lte=cutoff)
                .order_by("expiration_date")
            )
            if not items:
                continue

            to_email = business.notification_email
            if not to_email:
                self.stdout.write(self.style.WARNING(f"Skipping {business.name}: no email on file"))
                continue

            lines = [f"Products expiring within {business.notify_days_before} days:", ""]
            for item in items:
                days_left = (item.expiration_date - today).days
                status = "EXPIRED" if days_left < 0 else f"{days_left} days"
                lines.append(f"- {item.product.name}: {item.expiration_date} ({status}), quantity {item.quantity}")

            send_mail(
                subject=f"[Expiration Tracker] {items.count()} products need attention — {business.name}",
                message="\n".join(lines),
                from_email=None,
                recipient_list=[to_email],
            )
            items.update(notified_at=timezone.now())
            sent_count += 1
            self.stdout.write(self.style.SUCCESS(f"Notified {business.name} ({to_email}) about {items.count()} items"))

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {sent_count} notification email(s)."))
