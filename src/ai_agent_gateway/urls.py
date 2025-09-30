from django.urls import path
from . import views

app_name = 'ai_agent_gateway'

urlpatterns = [
    path('prompt/', views.handle_prompt, name='handle_prompt'),
    path('triggers/', views.trigger_list, name='trigger_list'),
    path('triggers/create/', views.create_trigger, name='create_trigger'),
]
