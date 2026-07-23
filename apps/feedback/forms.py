from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
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
        model = Feedback
        fields = ("category", "name", "email", "message")
        labels = {
            "category": "Category",
            "name": "Name (optional)",
            "email": "Email (optional)",
            "message": "Message",
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if not message:
            raise forms.ValidationError("Please enter a message.")
        return message
