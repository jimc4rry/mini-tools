import datetime

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

WELLNESS_TRIAL_LENGTH_DAYS = 14


class WellnessProfile(models.Model):
    class Sex(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    class ActivityLevel(models.TextChoices):
        SEDENTARY = "sedentary", _("Sedentary (little/no exercise)")
        MODERATE = "moderate", _("Moderate (exercise 3-5x/week)")
        ACTIVE = "active", _("Active (hard exercise 6-7x/week)")

    # Standard Harris-Benedict activity multipliers, commonly paired with
    # Mifflin-St Jeor for a Total Daily Energy Expenditure estimate.
    ACTIVITY_MULTIPLIERS = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.MODERATE: 1.55,
        ActivityLevel.ACTIVE: 1.725,
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wellness_profile"
    )
    sex = models.CharField(max_length=10, choices=Sex.choices, verbose_name=_("Biological sex"))
    age = models.PositiveSmallIntegerField(verbose_name=_("Age"))
    height_cm = models.PositiveSmallIntegerField(verbose_name=_("Height (cm)"))
    goal_weight_kg = models.DecimalField(
        max_digits=5, decimal_places=1, verbose_name=_("Goal weight (kg)")
    )
    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.MODERATE,
        verbose_name=_("Activity level"),
    )
    start_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Wellness profile for {self.user}"

    @property
    def current_weight_kg(self):
        latest = self.user.weight_logs.order_by("-date").first()
        return latest.weight_kg if latest else None

    def bmr(self):
        """
        Mifflin-St Jeor Basal Metabolic Rate. Needs a logged current weight -
        returns None until the user has at least one WeightLog entry.
        """
        weight = self.current_weight_kg
        if weight is None:
            return None
        base = 10 * float(weight) + 6.25 * self.height_cm - 5 * self.age
        return round(base + 5 if self.sex == self.Sex.MALE else base - 161)

    def tdee(self):
        """Total Daily Energy Expenditure - BMR scaled by activity level."""
        bmr = self.bmr()
        if bmr is None:
            return None
        return round(bmr * self.ACTIVITY_MULTIPLIERS[self.activity_level])

    def weeks_to_goal(self):
        """
        Deliberately NOT derived from a theoretical calorie deficit - this app
        doesn't track intake, so BMR/TDEE alone can't predict a real-world
        rate of change. Instead this extrapolates from the user's *actual*
        logged trend over their last 14 weigh-ins, falling back to a
        conservative 0.5kg/week assumption only until there's enough history
        to trust (or if the trend isn't actually moving toward the goal yet).
        """
        current = self.current_weight_kg
        if current is None:
            return None

        remaining = float(current) - float(self.goal_weight_kg)
        if remaining <= 0:
            return 0

        logs = list(self.user.weight_logs.order_by("-date")[:14])
        if len(logs) >= 2:
            days_span = (logs[0].date - logs[-1].date).days or 1
            actual_change = float(logs[-1].weight_kg) - float(logs[0].weight_kg)
            weekly_rate = (actual_change / days_span) * 7
            if weekly_rate > 0.05:
                return round(remaining / weekly_rate, 1)

        assumed_weekly_rate = 0.5
        return round(remaining / assumed_weekly_rate, 1)


class WeightLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weight_logs"
    )
    date = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, verbose_name=_("Weight (kg)"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}: {self.weight_kg}kg"


class Mission(models.Model):
    """
    The catalog of possible daily missions - not user-specific, just the pool
    that _todays_missions() (see views.py) picks 3 from each day.
    """

    text = models.CharField(max_length=200, verbose_name=_("Mission"))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.text


class DailyMissionLog(models.Model):
    """One row per (user, date, mission) - created the first time a user views that day's missions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mission_logs"
    )
    date = models.DateField()
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "date", "mission")

    def __str__(self):
        return f"{self.user} - {self.date}: {self.mission}"


class GraceDayLog(models.Model):
    """
    One row per (user, ISO week) - existence of a row means the weekly
    "Joker" has already been used that week. No penalty tracking on purpose -
    the whole point of the Grace System is that using it isn't a failure.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grace_days"
    )
    week_start = models.DateField()
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "week_start")

    @staticmethod
    def week_start_for(date):
        return date - datetime.timedelta(days=date.weekday())
