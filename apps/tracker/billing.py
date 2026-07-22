"""
Paddle Billing webhook handler.

Setup (once you have a real Paddle account):
1. Create a Product + Price in the Paddle dashboard for the monthly subscription.
2. When you build the checkout flow, pass `custom_data: {"business_id": business.id}`
   so this handler can map the Paddle subscription back to a Business.
3. Set PADDLE_WEBHOOK_SECRET in .env (Paddle dashboard -> Developer Tools -> Notifications
   -> your webhook destination -> signing secret).
4. Point the webhook destination at POST https://<your-domain>/expiration-tracker/billing/paddle-webhook/
   for events: subscription.created, subscription.updated, subscription.canceled.

Until PADDLE_WEBHOOK_SECRET is set, signature verification is skipped ONLY when DEBUG=True,
so the endpoint can be exercised locally with unsigned test payloads. In production
(DEBUG=False) an unset secret makes every request get rejected rather than silently trusted.
"""
import hashlib
import hmac
import ipaddress
import json
import logging

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Business

logger = logging.getLogger(__name__)

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
INACTIVE_SUBSCRIPTION_STATUSES = {"canceled", "paused"}

PADDLE_IPS_CACHE_KEY = "paddle_webhook_ip_ranges"
PADDLE_IPS_CACHE_TTL = 60 * 60 * 6  # 6 hours - these change rarely, per Paddle


def _paddle_webhook_ip_ranges():
    """Fetches and caches Paddle's current webhook-sending IPv4 ranges from their own
    /ips endpoint (never hardcoded - Paddle documents this list can change). Returns
    None on any failure so the caller can treat "unknown" differently from "mismatch"."""
    cached = cache.get(PADDLE_IPS_CACHE_KEY)
    if cached is not None:
        return cached
    try:
        response = requests.get("https://api.paddle.com/ips", timeout=5)
        response.raise_for_status()
        networks = [ipaddress.ip_network(cidr) for cidr in response.json()["data"]["ipv4_cidrs"]]
    except Exception:
        logger.exception("Could not fetch Paddle webhook IP ranges")
        return None
    cache.set(PADDLE_IPS_CACHE_KEY, networks, PADDLE_IPS_CACHE_TTL)
    return networks


def is_known_paddle_webhook_ip(remote_addr):
    """Checks remote_addr against Paddle's published webhook IP ranges - logging only,
    not enforced. This deployment sits behind Railway's proxy and REMOTE_ADDR has not
    been confirmed to reflect the real caller (vs. the proxy's own address), so a
    mismatch here is a signal to investigate, not proof the request is forged. The
    HMAC signature in _verify_signature() is the actual authentication - do not
    reject webhook requests based on this check without first confirming REMOTE_ADDR
    is trustworthy on this deployment (see the log line this produces)."""
    networks = _paddle_webhook_ip_ranges()
    if networks is None:
        return None  # couldn't fetch the list - unknown, not a mismatch
    try:
        ip = ipaddress.ip_address(remote_addr)
    except ValueError:
        return False
    return any(ip in network for network in networks)


def _verify_signature(request):
    secret = getattr(settings, "PADDLE_WEBHOOK_SECRET", "")
    if not secret:
        # Unsigned requests would let anyone flip any business's plan_status by guessing
        # a business_id. Only tolerate that in local dev; refuse outright once DEBUG=False.
        return settings.DEBUG

    header = request.headers.get("Paddle-Signature", "")
    parts = dict(p.split("=", 1) for p in header.split(";") if "=" in p)
    timestamp, signature = parts.get("ts"), parts.get("h1")
    if not timestamp or not signature:
        return False

    signed_payload = f"{timestamp}:{request.body.decode('utf-8')}"
    expected = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _find_business(data):
    custom_data = data.get("custom_data") or {}
    business_id = custom_data.get("business_id")
    if business_id:
        business = Business.objects.filter(pk=business_id).first()
        if business:
            return business

    customer_id = data.get("customer_id", "")
    subscription_id = data.get("id", "")
    return (
        Business.objects.filter(paddle_customer_id=customer_id).first()
        or Business.objects.filter(paddle_subscription_id=subscription_id).first()
    )


@csrf_exempt
@require_POST
def paddle_webhook(request):
    if not _verify_signature(request):
        return HttpResponseBadRequest("invalid signature")

    remote_addr = request.META.get("REMOTE_ADDR", "")
    known_ip = is_known_paddle_webhook_ip(remote_addr)
    if known_ip is False:
        logger.warning("Paddle webhook request from unrecognized IP %s (signature was valid)", remote_addr)

    try:
        payload = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("invalid json")

    event_type = payload.get("event_type", "")
    data = payload.get("data", {})

    business = _find_business(data)
    if business is None:
        # Acknowledge anyway so Paddle doesn't keep retrying an event we can't map.
        return HttpResponse(status=200)

    if event_type in ("subscription.created", "subscription.updated"):
        business.paddle_subscription_id = data.get("id", business.paddle_subscription_id)
        business.paddle_customer_id = data.get("customer_id", business.paddle_customer_id)
        status = data.get("status")
        if status in ACTIVE_SUBSCRIPTION_STATUSES:
            business.plan_status = Business.PlanStatus.ACTIVE
        elif status in INACTIVE_SUBSCRIPTION_STATUSES:
            business.plan_status = Business.PlanStatus.INACTIVE
        business.save()
    elif event_type == "subscription.canceled":
        business.plan_status = Business.PlanStatus.INACTIVE
        business.save()

    return HttpResponse(status=200)
