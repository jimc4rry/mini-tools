import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tools", "0006_seed_jira_helpers_tool"),
    ]

    operations = [
        migrations.AddField(
            model_name="tool",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
