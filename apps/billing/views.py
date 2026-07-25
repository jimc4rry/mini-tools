"""
Customer-facing checkout for paid apps on the Hub.

Each paid product (a `Subscription.product` slug — see models.py) gets an
"Upgrade" page here instead of inventing its own checkout flow. The page
loads Paddle.js (already included site-wide in templates/base.html),
initializes it with PADDLE_CLIENT_TOKEN, and opens an overlay checkout for
that product's Price ID (settings.PADDLE_PRICE_IDS).

This view never marks anything as paid - Paddle calls the webhook in
webhooks.py on successful checkout, and that's what flips the Subscription
(or, for Tracker specifically, the Business.plan_status field) to active.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

# Human-readable name shown on the upgrade page for each product slug.
# Add an entry here whenever a new paid app is wired up to billing.
PRODUCT_LABELS = {
    "tracker": "Expiration Tracker",
    "vault": "License & Subscription Vault",
}


@login_required
def upgrade(request, product):
    price_id = settings.PADDLE_PRICE_IDS.get(product)
    if not price_id:
        # No Price ID configured yet for this product - fail loudly instead of
        # opening a Paddle overlay that can't actually charge anyone.
        raise Http404("Upgrade isn't available for this product yet.")

    context = {
        "product": product,
        "product_label": PRODUCT_LABELS.get(product, product),
        "paddle_client_token": settings.PADDLE_CLIENT_TOKEN,
        "paddle_environment": settings.PADDLE_ENVIRONMENT,
        "paddle_price_id": price_id,
    }
    return render(request, "billing/upgrade.html", context)
