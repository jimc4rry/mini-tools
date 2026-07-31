import datetime
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import LogWeightForm, WellnessOnboardingForm, WellnessSettingsForm
from .models import DailyMissionLog, GraceDayLog, Mission, WeightLog, WellnessProfile


def _profile_or_none(user):
    try:
        return user.wellness_profile
    except WellnessProfile.DoesNotExist:
        return None


def _greeting(now):
    hour = now.hour
    if hour < 12:
        return _("Good morning - today is a fresh start.")
    if hour < 18:
        return _("Good afternoon - you're doing this for you.")
    return _("Good evening - one more consistent day, that's the whole game.")


def _todays_missions(user, today):
    """
    Same 3 missions all day for this user (stable on refresh), different
    tomorrow - seeded by (user_id, date) instead of pure random, so no
    background job is needed to "roll" them daily.
    """
    existing = DailyMissionLog.objects.filter(user=user, date=today).select_related("mission")
    if existing.exists():
        return existing

    pool = list(Mission.objects.filter(is_active=True))
    rng = random.Random(f"{user.id}-{today.isoformat()}")
    chosen = rng.sample(pool, min(3, len(pool)))
    DailyMissionLog.objects.bulk_create(
        [DailyMissionLog(user=user, date=today, mission=m) for m in chosen]
    )
    return DailyMissionLog.objects.filter(user=user, date=today).select_related("mission")


def _sparkline_points(logs):
    """
    Builds a simple SVG polyline from the last ~14 weigh-ins - a lightweight
    trend view without pulling in a JS charting library. `logs` is oldest-first.
    """
    if len(logs) < 2:
        return None
    values = [float(l.weight_kg) for l in logs]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    width, height = 280, 60
    step = width / (len(values) - 1)
    points = [
        f"{i * step:.1f},{height - ((v - lo) / span) * height:.1f}" for i, v in enumerate(values)
    ]
    return " ".join(points)


@login_required
def start_trial(request):
    """
    Sets up a Wellness profile for a platform account that doesn't have one
    yet (mirrors apps.tracker.views.start_trial / apps.vault.views.start_trial).
    """
    if _profile_or_none(request.user):
        return redirect("wellness:dashboard")

    if request.method == "POST":
        form = WellnessOnboardingForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            messages.success(request, _("Welcome! Let's build some consistency together."))
            return redirect("wellness:dashboard")
    else:
        form = WellnessOnboardingForm()
    return render(request, "wellness/start_trial.html", {"form": form})


@login_required
def dashboard(request):
    """
    Deliberately just three things on screen: today's weight, today's 3
    missions, and a time-of-day greeting - per the "no diet anxiety" brief,
    no calorie counts, no red "failure" states anywhere on this page.
    """
    profile = _profile_or_none(request.user)
    if profile is None:
        # Unlike Tracker/Vault, superusers are NOT bounced to Platform Admin
        # here - this app is built for the site owner's own daily use, not
        # just as an admin oversight tool, so everyone gets the same
        # onboarding path.
        return redirect("wellness:start_trial")

    today = timezone.localdate()
    missions = _todays_missions(request.user, today)

    week_start = GraceDayLog.week_start_for(today)
    joker_used_this_week = GraceDayLog.objects.filter(
        user=request.user, week_start=week_start
    ).exists()

    recent_logs = list(WeightLog.objects.filter(user=request.user).order_by("-date")[:14])
    sparkline = _sparkline_points(list(reversed(recent_logs)))

    context = {
        "profile": profile,
        "current_weight": profile.current_weight_kg,
        "missions": missions,
        "greeting": _greeting(timezone.localtime()),
        "weeks_to_goal": profile.weeks_to_goal(),
        "joker_available": not joker_used_this_week,
        "sparkline_points": sparkline,
        "already_logged_today": WeightLog.objects.filter(user=request.user, date=today).exists(),
    }
    return render(request, "wellness/dashboard.html", context)


@login_required
@require_POST
def log_weight(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return redirect("wellness:start_trial")

    form = LogWeightForm(request.POST)
    if form.is_valid():
        form.save(request.user)
        messages.success(request, _("Weight logged. Nice and steady."))
    else:
        messages.error(request, _("Please enter a valid weight."))
    return redirect("wellness:dashboard")


@login_required
@require_POST
def toggle_mission(request, pk):
    log = get_object_or_404(DailyMissionLog, pk=pk, user=request.user)
    log.is_completed = not log.is_completed
    log.save(update_fields=["is_completed"])
    return redirect("wellness:dashboard")


@login_required
@require_POST
def use_grace_day(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return redirect("wellness:start_trial")

    today = timezone.localdate()
    week_start = GraceDayLog.week_start_for(today)
    _log, created = GraceDayLog.objects.get_or_create(user=request.user, week_start=week_start)
    if created:
        messages.success(
            request,
            _("Enjoy it - slowly and on purpose. That's the whole point of the Joker."),
        )
    else:
        messages.info(request, _("You've already used this week's Joker."))
    return redirect("wellness:dashboard")


@login_required
def settings_view(request):
    profile = _profile_or_none(request.user)
    if profile is None:
        return redirect("wellness:start_trial")

    if request.method == "POST":
        form = WellnessSettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, _("Settings updated."))
            return redirect("wellness:settings")
    else:
        form = WellnessSettingsForm(instance=profile)
    return render(request, "wellness/settings.html", {"form": form})
