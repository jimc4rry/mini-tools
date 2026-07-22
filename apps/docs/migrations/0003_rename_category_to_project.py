from django.db import migrations, models


def rename_liteqa_project(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="liteqa").update(
        name="LiteQA – Lightweight Test Cases & Plans (Jira)"
    )


def revert_liteqa_project_name(apps, schema_editor):
    Project = apps.get_model("docs", "Project")
    Project.objects.filter(slug="liteqa").update(name="LiteQA")


class Migration(migrations.Migration):
    dependencies = [
        ("docs", "0002_seed_liteqa_docs"),
    ]

    operations = [
        migrations.RenameModel(old_name="Category", new_name="Project"),
        migrations.RenameField(model_name="document", old_name="category", new_name="project"),
        migrations.AlterModelOptions(
            name="project",
            options={"ordering": ["name"]},
        ),
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.RunPython(rename_liteqa_project, revert_liteqa_project_name),
    ]
