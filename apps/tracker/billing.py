"""
Paddle Billing webhook handler.

Setup (once you have a real Paddle account):
1. Create a Product + Price in the Paddle dashboard for the monthly subscription.
2. When you build the checkout flow, pass `custom_data: {"business_id": business.id}`
   so this handler can map the Paddle subscription back to a Business.
3. Set PADDLE_WEBHOOK_SECRET in .env (Paddle dashboard -> Developer Tools -> Notifications
   -> your webhook destination -> signing secret).
4. Point the webhook destination at POST https://<your-domain>/billing/paddle-webhook/
   for events: subscription.created, subscription.updated, subscription.canceled.

Until PADDLE_WEBHOOK_SECRET is set, signature verification is skipped ONLY when DEBUG=True,
so the endpoint can be exercised locally with unsigned test payloads. In production
(DEBUG=False) an unset secret makes every request get rejected rather than silently trusted.
"""
import hashlib
import hmac
import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Business

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
INACTIVE_SUBSCRIPTION_STATUSES = {"canceled", "paused"}


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
