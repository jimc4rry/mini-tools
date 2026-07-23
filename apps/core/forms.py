from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class PlatformSignupForm(UserCreationForm):
    """
    Universal, app-agnostic account creation - one login across the whole
    Hub. Picking an app/subscription (e.g. starting the Expiration
    Tracker's free trial) happens afterward, from the Tools/Applications
    page - not here.
    """

    email = forms.EmailField(required=True, label=_("Email"))
    # Honeypot: invisible to real users (off-screen, out of tab order, not read by
    # screen readers), so only a bot that blindly fills every input will populate it.
    # Left blank by humans - checked in the view, never saved.
    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "tabindex": "-1",
            "aria-hidden": "true",
            "style": "position:absolute; left:-9999px; width:1px; height:1px;",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
