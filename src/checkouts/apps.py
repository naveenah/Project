import logging
from django.apps import AppConfig


class CheckoutsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "checkouts"

logger = logging.getLogger(__name__)
logger.info("checkouts app config loaded")
