import logging
"""
Admin configuration for the customers app.
"""

from django.contrib import admin
from .models import Customer

logger = logging.getLogger(__name__)

# Register your models here.
admin.site.register(Customer)
logger.info("Customer model registered with admin")
