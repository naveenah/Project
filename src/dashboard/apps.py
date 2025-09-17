"""
App configuration for the dashboard app.
"""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """
    Configuration for the dashboard app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
