import logging
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

logger = logging.getLogger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
logger.info("Celery DJANGO_SETTINGS_MODULE set to 'Project.settings'")

app = Celery('ai_agent_gateway')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
logger.info("Celery configuration loaded from Django settings.")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
logger.info("Celery autodiscovered tasks.")


@app.task(bind=True)
def debug_task(self):
    log_message = f'Request: {self.request!r}'
    logger.debug(log_message)
    print(log_message)
