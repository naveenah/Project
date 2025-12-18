DEFAULT_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    'allauth_ui',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    'widget_tweaks',
    'slippers',
    'django_celery_beat',
]

_CUSTOMER_INSTALLED_APPS = [
    # My apps
    'commando',
    'customers',
    'profiles',
    'subscriptions',
    'visits',
    'checkouts',
    'landing',
    # Agent Gateway apps
    'ai_agent_gateway.apps.AgentGatewayConfig',
]

_INSTALLED_APPS = DEFAULT_APPS + _CUSTOMER_INSTALLED_APPS