"""
This module contains the AppConfig for the subscriptions app.
"""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    """
    The AppConfig for the subscriptions app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "subscriptions"
