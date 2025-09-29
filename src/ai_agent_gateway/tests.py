import re
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
import json
from .models import AgentTrigger
from .tasks import process_agent_action, check_scheduled_triggers, check_periodic_triggers
import datetime
from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st, settings

# Strategy for text that avoids null characters and surrogates
safe_text = st.text(
    alphabet=st.characters(
        min_codepoint=1,
        max_codepoint=0x10FFFF,
        blacklist_categories=('Cs',)  # Exclude surrogate characters
    )
)

# Strategy for JSON values that avoids surrogates and infinity
json_values = st.recursive(
    st.none() | st.booleans() | st.floats(allow_nan=False, allow_infinity=False) | safe_text,
    lambda children: st.lists(children) | st.dictionaries(safe_text, children),
    max_leaves=5
)

# Strategy for the top-level JSON object (must be a dictionary)
json_strategy = st.dictionaries(safe_text, json_values) | st.just({})

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

class AgentTriggerHypothesisTest(HypothesisTestCase):
    @given(
        name=safe_text.filter(lambda x: len(x) > 0 and len(x) <= 255),
        trigger_type=st.sampled_from([t[0] for t in AgentTrigger.TRIGGER_TYPES]),
        prompt_pattern=safe_text.filter(lambda x: len(x) <= 255) | st.none(),
        scheduled_time=st.datetimes(
            min_value=datetime.datetime(2020, 1, 1),
            max_value=datetime.datetime(2030, 1, 1),
        ).map(lambda dt: timezone.make_aware(dt, timezone.get_current_timezone())) | st.none(),
        periodic_interval=st.timedeltas(min_value=datetime.timedelta(seconds=1)) | st.none(),
        active=st.booleans(),
        action_payload=json_strategy,
    )
    @settings(deadline=None)
    def test_model_creation_with_hypothesis(self, name, trigger_type, prompt_pattern, scheduled_time, periodic_interval, active, action_payload):
        """Tests that the AgentTrigger model can be created with various data."""
        
        if trigger_type != 'prompt':
            prompt_pattern = None
        elif prompt_pattern is None:
            prompt_pattern = ".*"

        if trigger_type != 'scheduled':
            scheduled_time = None
        
        if trigger_type != 'periodic':
            periodic_interval = None

        AgentTrigger.objects.create(
            name=name,
            trigger_type=trigger_type,
            prompt_pattern=prompt_pattern,
            scheduled_time=scheduled_time,
            periodic_interval=periodic_interval,
            active=active,
            action_payload=action_payload
        )
        
        trigger = AgentTrigger.objects.get(name=name)
        self.assertEqual(trigger.name, name)
        self.assertEqual(trigger.trigger_type, trigger_type)

    @patch('ai_agent_gateway.views.process_agent_action.delay')
    @given(prompt=safe_text)
    @settings(deadline=None)
    def test_handle_prompt_hypothesis(self, mock_delay, prompt):
        """Tests the handle_prompt view with various prompt strings."""
        mock_delay.reset_mock()
        AgentTrigger.objects.all().delete()
        
        escaped_prompt = re.escape(prompt)
        trigger = AgentTrigger.objects.create(
            name='Hypothesis Trigger',
            trigger_type='prompt',
            prompt_pattern=f"^{escaped_prompt}$",
            active=True,
            action_payload={'message': 'Matched'}
        )

        client = Client()
        response = client.post(
            reverse('handle_prompt'),
            json.dumps({'prompt': prompt}),
            content_type='application/json'
        )

        if not prompt:
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['error'], 'Prompt is required')
            mock_delay.assert_not_called()
            return

        self.assertEqual(response.status_code, 200)
        
        if re.search(f"^{escaped_prompt}$", prompt):
            self.assertEqual(response.json()['message'], f'Trigger {trigger.name} activated')
            mock_delay.assert_called_once_with(trigger.id, trigger.action_payload)
        else:
            self.assertEqual(response.json()['message'], 'No matching triggers found')
            mock_delay.assert_not_called()
