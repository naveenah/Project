# agent_gateway/apps.py
from django.apps import AppConfig
from django.conf import settings

class AgentGatewayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agent_gateway'

    def ready(self):
        """
        Executes when the Django application is ready.

        Checks if 'celery' is included in the INSTALLED_APPS setting. If it is,
        this method dynamically configures the Celery Beat schedule to run the
        `check_scheduled_triggers` and `check_periodic_triggers` tasks every
        minute using crontab scheduling. This ensures that the trigger checks
        are performed regularly by the Celery Beat scheduler process.
        """
        if 'celery' in settings.INSTALLED_APPS:
            from . import tasks
            from celery.schedules import crontab
            from celery.beat import crontab_to_periodic

            from celery import current_app as celery_app

            celery_app.conf.beat_schedule = {
                'check-scheduled-triggers': {
                    'task': 'agent_gateway.tasks.check_scheduled_triggers',
                    'schedule': crontab(minute='*'), # Check every minute
                },
                'check-periodic-triggers': {
                    'task': 'agent_gateway.tasks.check_periodic_triggers',
                    'schedule': crontab(minute='*'), # Check every minute
                },
            }