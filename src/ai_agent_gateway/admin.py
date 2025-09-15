from django.contrib import admin
from .models import AgentTrigger

@admin.register(AgentTrigger)
class AgentTriggerAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'active', 'last_triggered')
    list_filter = ('trigger_type', 'active')
    search_fields = ('name', 'prompt_pattern')
