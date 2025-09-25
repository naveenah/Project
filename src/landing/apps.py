"""
App configuration for the landing app.
"""

from django.apps import AppConfig


class LandingConfig(AppConfig):
    """
    Configuration for the landing app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "landing"
