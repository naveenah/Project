import logging
from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auth"

logger = logging.getLogger(__name__)
logger.info("auth app config loaded")
