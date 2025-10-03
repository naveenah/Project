.. _usage:

Usage Guide
===========

This guide provides instructions for getting the project set up and configured.

Getting Started
---------------

**Logrean** is a Django-based web application that provides a robust platform for managing user subscriptions, profiles, and an AI agent gateway. The project is structured into several modular applications to ensure separation of concerns and scalability.

Key applications include:
- **genapp**: The core application containing project-wide settings and configurations.
- **ai_agent_gateway**: Manages AI agent triggers and asynchronous tasks.
- **auth**: Handles user authentication views.
- **checkouts**: Manages the Stripe checkout and payment finalization process.
- **commando**: Contains custom management commands.
- **customers**: Handles the mapping between users and Stripe customers.
- **dashboard**: Provides the main user dashboard after login.
- **helpers**: A collection of utility functions for billing, dates, and more.
- **landing**: Renders the public-facing landing page.
- **profiles**: Governs user profiles and related views.
- **subscriptions**: Manages subscription plans, pricing, and user entitlements.
- **visits**: Tracks page visits for analytics.

Installation
------------

To get the project running locally, follow these steps:

1.  **Clone the repository:**

    .. code-block:: bash

       git clone https://github.com/naveenah/Project.git
       cd Project

2.  **Install dependencies:**
    It is recommended to use a virtual environment.

    .. code-block:: bash

       python -m venv venv
       source venv/bin/activate
       pip install -r requirements.txt

3.  **Apply database migrations:**

    .. code-block:: bash

       python src/manage.py migrate

4.  **Run the development server:**

    .. code-block:: bash

       python src/manage.py runserver

Configuration
-------------

The project's behavior is controlled by environment variables, which are loaded in `src/genapp/settings.py`. Below are some of the key configuration variables:

.. confval:: SECRET_KEY

   **Type:** string

   A secret key for a particular Django installation. This is used to provide cryptographic signing and should be set to a unique, unpredictable value.

.. confval:: DEBUG

   **Type:** boolean

   **Default:** `False`

   A boolean that turns on/off debug mode. Never deploy a site into production with `DEBUG` turned on.

.. confval:: ALLOWED_HOSTS

   **Type:** list of strings

   A list of strings representing the host/domain names that this Django site can serve.

.. confval:: EMAIL_BACKEND

   **Type:** string

   **Default:** `django.core.mail.backends.smtp.EmailBackend`

   The backend to use for sending emails.

.. confval:: DATABASE_URL

   **Type:** string

   A URL-formatted string to configure the database connection (e.g., `postgres://user:password@host:port/dbname`).

.. confval:: STRIPE_SECRET_KEY

   **Type:** string

   Your secret key for the Stripe API, used for processing payments and managing subscriptions.
