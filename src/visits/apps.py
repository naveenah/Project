import logging
from django.apps import AppConfig


class VisitsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "visits"

logger = logging.getLogger(__name__)
logger.info("visits app config loaded")
