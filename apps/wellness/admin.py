from django.contrib import admin

from .models import DailyMissionLog, GraceDayLog, Mission, WeightLog, WellnessProfile


@admin.register(WellnessProfile)
class WellnessProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "sex", "age", "goal_weight_kg", "activity_level", "start_date")
    list_filter = ("sex", "activity_level")
    search_fields = ("user__username", "user__email")


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "weight_kg")
    list_filter = ("date",)
    search_fields = ("user__username",)
    date_hierarchy = "date"


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("text", "is_active")
    list_filter = ("is_active",)
    search_fields = ("text",)


@admin.register(DailyMissionLog)
class DailyMissionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "mission", "is_completed")
    list_filter = ("date", "is_completed")
    search_fields = ("user__username",)


@admin.register(GraceDayLog)
class GraceDayLogAdmin(admin.ModelAdmin):
    list_display = ("user", "week_start", "used_at")
    search_fields = ("user__username",)
