import logging
"""
This module registers the Subscription, SubscriptionPrice, and UserSubscription
models with the Django admin site.
"""

from django.contrib import admin

# Register your models here.
from .models import Subscription, SubscriptionPrice, UserSubscription

logger = logging.getLogger(__name__)

class SubscriptionPriceInline(admin.StackedInline):
    """
    An inline admin for the SubscriptionPrice model.
    """
    model = SubscriptionPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0

class SubscriptionAdmin(admin.ModelAdmin):
    """
    The admin for the Subscription model.
    """
    inlines = [SubscriptionPriceInline]
    list_display = ['name', 'active']
    readonly_fields = ['stripe_id']

admin.site.register(Subscription, SubscriptionAdmin) 
admin.site.register(UserSubscription)

logger.info("Subscription models registered with admin.")