# Generated by Django 5.1.3 on 2025-01-22 12:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0017_usersubscription_user_cancelled"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersubscription",
            name="current_period_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="current_period_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="original_period_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
