import logging
from django.apps import AppConfig


class CommandoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "commando"

logger = logging.getLogger(__name__)
logger.info("commando app config loaded")
