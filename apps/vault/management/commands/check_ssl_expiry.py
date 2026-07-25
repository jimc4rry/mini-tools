import datetime
import socket
import ssl

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.vault.models import VaultItem

CHECK_TIMEOUT_SECONDS = 10


def fetch_cert_expiry(domain):
    """
    Connects to domain:443 and reads the real certificate's expiry date -
    no scraping, no third-party API, just a standard TLS handshake (the same
    thing a browser does when you visit the site).
    """
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=CHECK_TIMEOUT_SECONDS) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            cert = ssock.getpeercert()
    not_after = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
    return not_after.date()


class Command(BaseCommand):
    help = (
        "Checks the real SSL certificate expiry for every Vault item with "
        "auto_check_domain set, and keeps expires_at in sync automatically."
    )

    def handle(self, *args, **options):
        items = VaultItem.objects.filter(is_active=True).exclude(auto_check_domain="")
        checked, failed = 0, 0

        for item in items:
            domain = item.auto_check_domain.strip()
            try:
                expiry_date = fetch_cert_expiry(domain)
            except Exception as exc:
                item.last_check_error = str(exc)[:255]
                item.last_checked_at = timezone.now()
                item.save(update_fields=["last_check_error", "last_checked_at"])
                failed += 1
                self.stdout.write(self.style.WARNING(f"{domain}: {exc}"))
                continue

            item.expires_at = expiry_date
            item.last_checked_at = timezone.now()
            item.last_check_error = ""
            item.save(update_fields=["expires_at", "last_checked_at", "last_check_error"])
            checked += 1
            self.stdout.write(self.style.SUCCESS(f"{domain}: certificate expires {expiry_date}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Checked {checked}, failed {failed}."))
