import logging
"""
App configuration for the customers app.
"""

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CustomersConfig(AppConfig):
    """
    Configuration for the customers app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "customers"

    def ready(self):
        """
        Signal connection for the customers app.
        """
        logger.info("Customers app ready.")
        from . import signals  # noqa
