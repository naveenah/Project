import logging
"""
Admin configuration for the dashboard app.
"""

from django.contrib import admin

# Register your models here.

logger = logging.getLogger(__name__)
logger.info("dashboard admin loaded")
