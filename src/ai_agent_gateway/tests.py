from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
import json
from .models import AgentTrigger
from .tasks import process_agent_action, check_scheduled_triggers, check_periodic_triggers
import datetime

class AgentTriggerModelTest(TestCase):
    def test_agent_trigger_creation(self):
        trigger = AgentTrigger.objects.create(
            name='Test Trigger',
            trigger_type='prompt',
            prompt_pattern='hello',
            active=True,
            action_payload={'message': 'Hello, world!'}
        )
        self.assertEqual(str(trigger), 'Test Trigger')

class AgentGatewayViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.trigger = AgentTrigger.objects.create(
            name='Test Prompt Trigger',
            trigger_type='prompt',
            prompt_pattern='^hello$',
            active=True,
            action_payload={'message': 'Hello, world!'}
        )

    @patch('ai_agent_gateway.views.process_agent_action.delay')
    def test_handle_prompt_success(self, mock_delay):
        response = self.client.post(
            reverse('handle_prompt'),
            json.dumps({'prompt': 'hello'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], f'Trigger {self.trigger.name} activated')
        mock_delay.assert_called_once_with(self.trigger.id, self.trigger.action_payload)

    def test_handle_prompt_no_match(self):
        response = self.client.post(
            reverse('handle_prompt'),
            json.dumps({'prompt': 'goodbye'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'No matching triggers found')

    def test_trigger_list_view(self):
        response = self.client.get(reverse('trigger_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'agent_gateway/trigger_list.html')

    def test_create_trigger_view(self):
        response = self.client.post(reverse('create_trigger'), {
            'name': 'New Trigger',
            'trigger_type': 'prompt',
            'prompt_pattern': 'new',
            'action_payload': '{"key": "value"}',
            'active': 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AgentTrigger.objects.filter(name='New Trigger').exists())

class AgentGatewayTasksTest(TestCase):
    @patch('ai_agent_gateway.tasks.logger.info')
    def test_process_agent_action(self, mock_logger):
        trigger = AgentTrigger.objects.create(
            name='Task Test Trigger',
            trigger_type='prompt',
            action_payload={'message': 'Task test'}
        )
        process_agent_action(trigger.id, trigger.action_payload)
        trigger.refresh_from_db()
        self.assertIsNotNone(trigger.last_triggered)
        mock_logger.assert_called_with(f"Trigger {trigger.name} fired with payload: {trigger.action_payload}")

    @patch('ai_agent_gateway.tasks.process_agent_action.delay')
    def test_check_scheduled_triggers(self, mock_delay):
        scheduled_time = timezone.now() - datetime.timedelta(minutes=1)
        trigger = AgentTrigger.objects.create(
            name='Scheduled Trigger',
            trigger_type='scheduled',
            scheduled_time=scheduled_time,
            active=True,
            action_payload={'message': 'Scheduled task'}
        )
        check_scheduled_triggers()
        mock_delay.assert_called_once_with(trigger.id, trigger.action_payload)
        trigger.refresh_from_db()
        self.assertIsNone(trigger.scheduled_time)

    @patch('ai_agent_gateway.tasks.process_agent_action.delay')
    def test_check_periodic_triggers(self, mock_delay):
        interval = datetime.timedelta(minutes=5)
        last_triggered = timezone.now() - datetime.timedelta(minutes=6)
        trigger = AgentTrigger.objects.create(
            name='Periodic Trigger',
            trigger_type='periodic',
            periodic_interval=interval,
            last_triggered=last_triggered,
            active=True,
            action_payload={'message': 'Periodic task'}
        )
        check_periodic_triggers()
        mock_delay.assert_called_once_with(trigger.id, trigger.action_payload)
