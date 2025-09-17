"""
Admin configuration for the customers app.
"""

from django.contrib import admin
from .models import Customer

# Register your models here.
admin.site.register(Customer)
