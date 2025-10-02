import logging
"""
This module contains the AppConfig for the subscriptions app.
"""

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SubscriptionsConfig(AppConfig):
    """
    The AppConfig for the subscriptions app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "subscriptions"

    def ready(self):
        """
        Logs a message when the subscriptions app is ready.
        """
        logger.info("Subscriptions app ready.")
