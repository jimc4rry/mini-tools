import datetime

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.billing.models import Subscription

from .models import WELLNESS_TRIAL_LENGTH_DAYS, WeightLog, WellnessProfile


class WellnessOnboardingForm(forms.Form):
    """
    A couple of details plus today's weight to get started - mirrors
    apps.tracker.forms.BusinessOnboardingForm's shape (a plain Form, not a
    ModelForm, since it also creates the first WeightLog + Subscription).
    """

    sex = forms.ChoiceField(choices=WellnessProfile.Sex.choices, label=_("Biological sex"))
    age = forms.IntegerField(min_value=13, max_value=100, label=_("Age"))
    height_cm = forms.IntegerField(min_value=100, max_value=250, label=_("Height (cm)"))
    current_weight_kg = forms.DecimalField(
        min_value=30, max_value=300, decimal_places=1, label=_("Current weight (kg)")
    )
    goal_weight_kg = forms.DecimalField(
        min_value=30, max_value=300, decimal_places=1, label=_("Goal weight (kg)")
    )
    activity_level = forms.ChoiceField(
        choices=WellnessProfile.ActivityLevel.choices, label=_("Activity level")
    )

    def save(self, user):
        profile = WellnessProfile.objects.create(
            user=user,
            sex=self.cleaned_data["sex"],
            age=self.cleaned_data["age"],
            height_cm=self.cleaned_data["height_cm"],
            goal_weight_kg=self.cleaned_data["goal_weight_kg"],
            activity_level=self.cleaned_data["activity_level"],
        )
        WeightLog.objects.create(
            user=user,
            date=timezone.localdate(),
            weight_kg=self.cleaned_data["current_weight_kg"],
        )
        Subscription.objects.create(
            user=user,
            product="wellness",
            trial_ends_at=timezone.localdate() + datetime.timedelta(days=WELLNESS_TRIAL_LENGTH_DAYS),
        )
        return profile


class LogWeightForm(forms.Form):
    weight_kg = forms.DecimalField(min_value=30, max_value=300, decimal_places=1, label=_("Weight (kg)"))

    def save(self, user):
        today = timezone.localdate()
        entry, _created = WeightLog.objects.update_or_create(
            user=user, date=today, defaults={"weight_kg": self.cleaned_data["weight_kg"]}
        )
        return entry


class WellnessSettingsForm(forms.ModelForm):
    class Meta:
        model = WellnessProfile
        fields = ["goal_weight_kg", "activity_level", "age", "height_cm"]
