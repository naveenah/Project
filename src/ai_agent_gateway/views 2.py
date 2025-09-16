# agent_gateway/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
from .models import AgentTrigger
from .tasks import process_agent_action
from datetime import timedelta

@csrf_exempt
def handle_prompt(request):
    """
    Handles incoming prompts and triggers the appropriate agent action.

    This view expects a POST request with a JSON payload containing a "prompt" key.
    It searches for active, prompt-based triggers that match the received prompt
    and, if a match is found, dispatches a task to process the agent action.

    Args:
        request: The incoming HTTP request.

    Returns:
        A JSON response indicating whether a trigger was activated, no triggers
        were found, or an error occurred.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        prompt = data.get('prompt')
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)

        triggers = AgentTrigger.objects.filter(trigger_type='prompt', active=True)
        
        for trigger in triggers:
            if re.match(trigger.prompt_pattern, prompt):
                process_agent_action.delay(trigger.id, trigger.action_payload)
                return JsonResponse({'message': f'Trigger {trigger.name} activated'})

        return JsonResponse({'message': 'No matching triggers found'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
def trigger_list(request):
    """
    Displays a list of all configured agent triggers.

    Args:
        request: The incoming HTTP request.

    Returns:
        A rendered HTML page displaying the list of triggers.
    """
    triggers = AgentTrigger.objects.all()
    return render(request, 'agent_gateway/trigger_list.html', {'triggers': triggers})

@csrf_exempt
def create_trigger(request):
    """
    Handles the creation of a new agent trigger.

    This view processes a POST request containing the trigger's configuration
    data and creates a new `AgentTrigger` instance.

    Args:
        request: The incoming HTTP request.

    Returns:
        A redirect to the trigger list page.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        trigger_type = request.POST.get('trigger_type')
        prompt_pattern = request.POST.get('prompt_pattern')
        scheduled_time = request.POST.get('scheduled_time')
        periodic_interval = request.POST.get('periodic_interval')
        action_payload = request.POST.get('action_payload')
        active = request.POST.get('active') == 'on'

        try:
            action_payload_json = json.loads(action_payload)
        except json.JSONDecodeError:
            action_payload_json = {}

        periodic_interval_delta = None
        if periodic_interval:
          try:
            days, time = periodic_interval.split(' ')
            hours, minutes, seconds = time.split(':')
            periodic_interval_delta = timedelta(days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds))
          except ValueError:
            periodic_interval_delta=None

        AgentTrigger.objects.create(
            name=name,
            trigger_type=trigger_type,
            prompt_pattern=prompt_pattern,
            scheduled_time=scheduled_time,
            periodic_interval=periodic_interval_delta,
            action_payload=action_payload_json,
            active=active,
        )
        return redirect('trigger_list')
    return redirect('trigger_list') # Handles get request.