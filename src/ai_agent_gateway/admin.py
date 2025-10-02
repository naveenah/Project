import logging
from django.contrib import admin
from .models import AgentTrigger

logger = logging.getLogger(__name__)

@admin.register(AgentTrigger)
class AgentTriggerAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'active', 'last_triggered')
    list_filter = ('trigger_type', 'active')
    search_fields = ('name', 'prompt_pattern')

    def save_model(self, request, obj, form, change):
        logger.info(f"Saving AgentTrigger: {obj.name} by user {request.user.username}")
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        logger.warning(f"Deleting AgentTrigger: {obj.name} by user {request.user.username}")
        super().delete_model(request, obj)
