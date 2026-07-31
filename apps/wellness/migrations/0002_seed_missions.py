from django.db import migrations

MISSIONS = [
    "Drink 2 litres of water today",
    "Take a 10-minute walk after a meal",
    "Eat protein with breakfast",
    "Get 7+ hours of sleep tonight",
    "Eat a piece of fruit instead of a snack today",
    "Stretch for 5 minutes when you wake up",
    "Take the stairs instead of the elevator today",
    "Cook one meal at home instead of ordering out",
    "Add a vegetable to your next meal",
    "Stand up and move for 2 minutes every hour",
    "Prep tomorrow's breakfast tonight",
    "Take 3 deep breaths before your next meal",
]


def seed_missions(apps, schema_editor):
    Mission = apps.get_model("wellness", "Mission")
    for text in MISSIONS:
        Mission.objects.update_or_create(text=text, defaults={"is_active": True})


def remove_missions(apps, schema_editor):
    Mission = apps.get_model("wellness", "Mission")
    Mission.objects.filter(text__in=MISSIONS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("wellness", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_missions, remove_missions),
    ]
