# Generated by Django 5.1.3 on 2025-01-31 12:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0018_usersubscription_current_period_end_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersubscription",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("active", "ACTIVE"),
                    ("trailing", "TRAILING"),
                    ("incomplete", "INCOMPLETE"),
                    ("incomplete_expired", "INCOMPLETE_EXPIRED"),
                    ("past_due", "PAST_DUE"),
                    ("cancelled", "CANCELLED"),
                    ("unpaid", "UNPAID"),
                    ("paused", "PAUSED"),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
