# Generated by Django 5.1.3 on 2024-12-14 14:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("subscriptions", "0002_alter_subscription_options_subscription_groups"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="subscription",
            options={
                "permissions": [
                    ("advanced", "Advanced Perm"),
                    ("pro", "Pro Perm"),
                    ("basic", "Basic Perm"),
                    ("basic_ai", "Basic AI Perm"),
                ]
            },
        ),
        migrations.AddField(
            model_name="subscription",
            name="permissions",
            field=models.ManyToManyField(
                limit_choices_to={
                    "codename__in": ["advanced", "pro", "basic", "basic_ai"],
                    "content_type__app_label": "subscriptions",
                },
                to="auth.permission",
            ),
        ),
    ]
