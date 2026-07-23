from django import forms

from .models import Subscription


class PlatformSubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ("status", "trial_ends_at", "paddle_subscription_id", "paddle_customer_id")
        widgets = {
            "trial_ends_at": forms.DateInput(attrs={"type": "date"}),
        }
