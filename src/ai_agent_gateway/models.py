# agent_gateway/models.py
from django.db import models
from django.utils import timezone

class AgentTrigger(models.Model):
    """
    Represents a trigger for an AI agent action.

    Attributes:
        name (str): A descriptive name for the trigger.
        trigger_type (str): The type of trigger, chosen from TRIGGER_TYPES.
        prompt_pattern (str, optional): A regex pattern to match against incoming prompts.
            Used when trigger_type is 'prompt'.
        scheduled_time (datetime, optional): The specific time to trigger the action.
            Used when trigger_type is 'scheduled'.
        periodic_interval (timedelta, optional): The interval at which to trigger the action.
            Used when trigger_type is 'periodic'.
        last_triggered (datetime, optional): The last time the trigger was activated.
        active (bool): Whether the trigger is currently active.
        action_payload (dict): A JSON object containing instructions for the agent.
    """
    TRIGGER_TYPES = (
        ('prompt', 'Prompt'),
        ('scheduled', 'Scheduled'),
        ('periodic', 'Periodic'),
    )
    name = models.CharField(max_length=255)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    prompt_pattern = models.CharField(max_length=255, blank=True, null=True, help_text="Regex pattern for prompt trigger")
    scheduled_time = models.DateTimeField(blank=True, null=True, help_text="Time for scheduled trigger")
    periodic_interval = models.DurationField(blank=True, null=True, help_text="Interval for periodic trigger")
    last_triggered = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)
    action_payload = models.JSONField(default=dict) #Store instructions for the agent

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['trigger_type', 'active']),
        ]
