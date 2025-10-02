import logging
"""
App configuration for the dashboard app.
"""

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class DashboardConfig(AppConfig):
    """
    Configuration for the dashboard app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        """
        Logs a message when the dashboard app is ready.
        """
        logger.info("Dashboard app ready.")
