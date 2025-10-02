import logging
"""
App configuration for the landing app.
"""

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class LandingConfig(AppConfig):
    """
    Configuration for the landing app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "landing"

    def ready(self):
        """
        Logs a message when the landing app is ready.
        """
        logger.info("Landing app ready.")
