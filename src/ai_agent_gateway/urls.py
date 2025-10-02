import logging
from django.urls import path
from . import views

logger = logging.getLogger(__name__)
logger.info("Loading URL patterns for ai_agent_gateway app.")

app_name = 'ai_agent_gateway'

urlpatterns = [
    path('prompt/', views.handle_prompt, name='handle_prompt'),
    path('triggers/', views.trigger_list, name='trigger_list'),
    path('triggers/create/', views.create_trigger, name='create_trigger'),
]
