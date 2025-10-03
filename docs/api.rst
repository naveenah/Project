.. _api:

API Reference
=============

This section provides a detailed reference for the project's core applications, models, views, and utility functions.

.. toctree::
   :maxdepth: 2
   :caption: API Modules:

Core Applications
-----------------

### Auth (`src/auth`)

.. automodule:: auth.views
   :members: login_view, register_view

### Checkouts (`src/checkouts`)

.. automodule:: checkouts.views
   :members: product_price_redirect_view, checkout_redirect_view, checkout_finalize_view

### Commando (`src/commando`)

.. automodule:: commando.models
   :members:

.. automodule:: commando.views
   :members:

### Customers (`src/customers`)

.. automodule:: customers.models
   :members: Customer

### Dashboard (`src/dashboard`)

.. automodule:: dashboard.models
   :members:

.. automodule:: dashboard.views
   :members: dashboard_view

### Helpers (`src/helpers`)

.. automodule:: helpers.billing
   :members: serialize_subscription_data, create_customer, create_product, create_price, start_checkout_session, get_checkout_session, get_subscription, get_customer_active_subscriptions, cancel_subscription, get_checkout_customer_plan

.. automodule:: helpers.date_utils
   :members: timestamp_as_datetime

.. automodule:: helpers.downloader
   :members: download_to_local

.. automodule:: helpers.numbers
   :members: shorten_number

### Landing (`src/landing`)

.. automodule:: landing.models
   :members:

.. automodule:: landing.views
   :members: landing_dashboard_page_view

### Profiles (`src/profiles`)

.. automodule:: profiles.models
   :members:

.. automodule:: profiles.views
   :members: profile_list_view, profile_detail_view

### Subscriptions (`src/subscriptions`)

.. automodule:: subscriptions.models
   :members: Subscription, SubscriptionPrice, UserSubscription

.. automodule:: subscriptions.views
   :members: user_subscription_view, user_subscription_cancel_view, subscription_price_view

### Visits (`src/visits`)

.. automodule:: visits.models
   :members: PageVisits

AI Agent Gateway (`src/ai_agent_gateway`)
-----------------------------------------

### Models

.. automodule:: ai_agent_gateway.models
   :members: AgentTrigger

### Views

.. automodule:: ai_agent_gateway.views
   :members: handle_prompt, trigger_list, create_trigger

### Asynchronous Tasks

.. automodule:: ai_agent_gateway.tasks
   :members: process_agent_action, check_scheduled_triggers, check_periodic_triggers
