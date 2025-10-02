import logging
"""
App configuration for the profiles app.
"""

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ProfilesConfig(AppConfig):
    """
    Configuration for the profiles app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "profiles"

    def ready(self):
        """
        Logs a message when the profiles app is ready.
        """
        logger.info("Profiles app ready.")
