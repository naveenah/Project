# AI Agent Gateway

The `ai_agent_gateway` is a Django application that acts as a flexible and extensible gateway for interacting with AI agents. It allows you to define triggers that, when activated, will cause an AI agent to perform a specific action.

## Key Features

*   **Multiple Trigger Types:** Supports various trigger types, including:
    *   **Prompt-based:** Triggers an agent action when a specific prompt is received.
    *   **Scheduled:** Triggers an agent action at a specific time.
    *   **Periodic:** Triggers an agent action at a regular interval.
*   **Asynchronous Task Processing:** Uses Celery to process agent actions asynchronously, ensuring that the application remains responsive.
*   **Extensible:** Can be easily extended to support new trigger types and agent integrations.

## How It Works

The application is built around the `AgentTrigger` model, which defines the conditions under which an agent action should be triggered. When a trigger's conditions are met, a Celery task is created to process the action.

The `ai_agent_gateway` provides a set of views for managing triggers, as well as a view for handling incoming prompts.

## Getting Started

1.  **Install the application:** Add `ai_agent_gateway` to your `INSTALLED_APPS` in your Django project's `settings.py` file.
2.  **Run the migrations:** Run `python manage.py migrate` to create the necessary database tables.
3.  **Create a trigger:** Use the Django admin interface or the provided views to create a new `AgentTrigger`.
4.  **Trigger an action:** Depending on the trigger type, you can trigger an action by sending a prompt, waiting for the scheduled time, or waiting for the periodic interval to elapse.

## Key Components

*   **`models.py`:** Defines the `AgentTrigger` model.
*   **`views.py`:** Contains the views for managing triggers and handling incoming prompts.
*   **`tasks.py`:** Contains the Celery tasks for processing agent actions.
*   **`admin.py`:** Registers the `AgentTrigger` model with the Django admin interface.
*   **`urls.py`:** Defines the URL patterns for the application.
