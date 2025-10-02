import logging
"""
Admin configuration for the landing app.
"""

from django.contrib import admin

# Register your models here.

logger = logging.getLogger(__name__)
logger.info("landing admin loaded")
