# agent_gateway/tasks.py (using Celery for asynchronous tasks)
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import AgentTrigger
import re
import requests  # Or your chosen agent interaction library
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_agent_action(trigger_id, payload):
    """
    Processes an agent action triggered by a specific event or schedule.

    This task is responsible for executing the action associated with a
    triggered `AgentTrigger`. It logs the action, interacts with the agent,
    and updates the trigger's `last_triggered` timestamp.

    Args:
        trigger_id: The ID of the `AgentTrigger` that was activated.
        payload: The action payload associated with the trigger.
    """
    try:
        trigger = AgentTrigger.objects.get(pk=trigger_id)
        # Replace with your actual agent interaction logic
        logger.info(f"Trigger {trigger.name} fired with payload: {payload}")
        # Example: Send payload to an external agent API
        # response = requests.post("your_agent_api_endpoint", json=payload)
        # print(response.json())
        trigger.last_triggered = timezone.now()
        trigger.save()

    except AgentTrigger.DoesNotExist:
        logger.info(f"Trigger with ID {trigger_id} not found.")
    except Exception as e:
        logger.info(f"Error processing trigger {trigger_id}: {e}")

from django.db.models import F, Q

@shared_task
def check_scheduled_triggers():
    """
    Checks for and processes scheduled triggers that are due.
    """
    now = timezone.now()
    triggers = AgentTrigger.objects.filter(
        trigger_type='scheduled', 
        scheduled_time__lte=now, 
        active=True
    )
    
    trigger_ids = []
    for trigger in triggers:
        process_agent_action.delay(trigger.id, trigger.action_payload)
        trigger_ids.append(trigger.id)
    
    if trigger_ids:
        # Bulk update to avoid N+1 queries
        AgentTrigger.objects.filter(id__in=trigger_ids).update(scheduled_time=None, last_triggered=now)

@shared_task
def check_periodic_triggers():
    """
    Checks for and processes periodic triggers that are due.
    """
    now = timezone.now()
    
    # Efficiently filter for due periodic triggers in the database
    due_triggers = AgentTrigger.objects.filter(
        trigger_type='periodic',
        active=True
    ).filter(
        Q(last_triggered__isnull=True) |
        Q(last_triggered__lte=now - F('periodic_interval'))
    )
    
    trigger_ids = [trigger.id for trigger in due_triggers]

    if trigger_ids:
        # Atomically update last_triggered to prevent race conditions
        updated_count = AgentTrigger.objects.filter(id__in=trigger_ids).update(last_triggered=now)
        
        if updated_count > 0:
            # Fetch the updated triggers to get the correct payload for the task
            updated_triggers = AgentTrigger.objects.filter(id__in=trigger_ids)
            for trigger in updated_triggers:
                process_agent_action.delay(trigger.id, trigger.action_payload)
