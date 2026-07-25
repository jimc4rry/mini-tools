import datetime

from django import forms
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.billing.models import Subscription

from .models import VAULT_TRIAL_LENGTH_DAYS, VaultItem, VaultProfile


class VaultOnboardingForm(forms.Form):
    """
    Starts the Vault free trial for an already logged-in platform account
    and sets their Master PIN in the same step (mirrors
    apps.tracker.forms.BusinessOnboardingForm).
    """

    pin = forms.CharField(
        label=_("Master PIN"),
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "new-password"}),
        min_length=4,
        max_length=12,
        help_text=_("4-12 digits. You'll need this to reveal or copy any stored secret."),
    )
    pin_confirm = forms.CharField(
        label=_("Confirm PIN"),
        widget=forms.PasswordInput(attrs={"inputmode": "numeric", "autocomplete": "new-password"}),
    )

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit():
            raise forms.ValidationError(_("PIN must be numeric."))
        return pin

    def clean(self):
        cleaned = super().clean()
        pin, confirm = cleaned.get("pin"), cleaned.get("pin_confirm")
        if pin and confirm and pin != confirm:
            raise forms.ValidationError(_("PINs don't match."))
        return cleaned

    def save(self, user):
        trial_ends_at = timezone.localdate() + datetime.timedelta(days=VAULT_TRIAL_LENGTH_DAYS)
        profile = VaultProfile.objects.create(
            user=user, pin_hash=make_password(self.cleaned_data["pin"])
        )
        Subscription.objects.create(user=user, product="vault", trial_ends_at=trial_ends_at)
        return profile


class ChangePinForm(forms.Form):
    current_pin = forms.CharField(label=_("Current PIN"), widget=forms.PasswordInput())
    new_pin = forms.CharField(
        label=_("New PIN"), widget=forms.PasswordInput(), min_length=4, max_length=12
    )
    new_pin_confirm = forms.CharField(label=_("Confirm new PIN"), widget=forms.PasswordInput())

    def __init__(self, *args, profile=None, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_current_pin(self):
        from django.contrib.auth.hashers import check_password

        pin = self.cleaned_data["current_pin"]
        if not check_password(pin, self.profile.pin_hash):
            raise forms.ValidationError(_("Incorrect PIN."))
        return pin

    def clean_new_pin(self):
        pin = self.cleaned_data["new_pin"]
        if not pin.isdigit():
            raise forms.ValidationError(_("PIN must be numeric."))
        return pin

    def clean(self):
        cleaned = super().clean()
        new_pin, confirm = cleaned.get("new_pin"), cleaned.get("new_pin_confirm")
        if new_pin and confirm and new_pin != confirm:
            raise forms.ValidationError(_("New PINs don't match."))
        return cleaned

    def save(self):
        self.profile.pin_hash = make_password(self.cleaned_data["new_pin"])
        self.profile.save(update_fields=["pin_hash"])
        return self.profile


class UnlockForm(forms.Form):
    pin = forms.CharField(widget=forms.PasswordInput())


class VaultItemForm(forms.ModelForm):
    class Meta:
        model = VaultItem
        fields = [
            "name",
            "item_type",
            "vendor",
            "secret_value",
            "notes",
            "billing_cycle",
            "cost_amount",
            "cost_currency",
            "expires_at",
            "auto_check_domain",
        ]
        widgets = {
            "secret_value": forms.Textarea(attrs={"rows": 3, "autocomplete": "off"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "expires_at": forms.DateInput(attrs={"type": "date"}),
            "auto_check_domain": forms.TextInput(attrs={"placeholder": "example.com"}),
        }
