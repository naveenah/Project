# GitHub Copilot Instructions - Django SaaS Platform

## Project Overview

This is a Django 5.1.x-based SaaS (Software as a Service) platform designed as a foundation for building subscription-based services. The application integrates with Stripe for payment processing, uses PostgreSQL for production databases, implements user authentication via Django Allauth, and includes an AI agent gateway system for automated task processing.

**Tech Stack:**
- **Framework:** Django 5.1.15
- **Python:** 3.13.0+
- **Database:** SQLite (development) / PostgreSQL (production via Neon)
- **Payment:** Stripe API
- **Authentication:** Django Allauth (email, username, GitHub OAuth)
- **Task Queue:** Celery + Redis + django-celery-beat
- **Static Files:** WhiteNoise with CompressedManifestStaticFilesStorage
- **UI:** Tailwind CSS (via Flowbite), custom SaaS theme
- **Config Management:** python-decouple for environment variables

## Architecture & Design Patterns

### Project Structure
```
src/                        # Main Django project root
├── genapp/                # Core project settings and configuration
├── customers/             # Customer management and Stripe integration
├── subscriptions/         # Subscription plans and user subscriptions
├── checkouts/            # Stripe checkout flow
├── auth/                 # Custom authentication views
├── profiles/             # User profile management
├── dashboard/            # Authenticated user dashboard
├── landing/              # Public landing page
├── visits/               # Page visit tracking
├── ai_agent_gateway/     # AI agent trigger system
├── commando/             # Custom management commands
├── helpers/              # Utility functions (billing, numbers, dates, downloader)
└── templates/            # Django templates
```

### Key Design Patterns

1. **Signal-Driven Architecture**: Uses Django signals extensively for:
   - Customer creation on user signup (`allauth_user_signed_up`)
   - Email confirmation triggers Stripe customer creation (`allauth_email_confirmed`)
   - Subscription updates trigger group/permission changes (`user_sub_post_save`)

2. **Stripe Integration Pattern**: All Stripe operations centralized in `helpers/billing.py`:
   - Wraps Stripe API calls with error handling and logging
   - Provides `raw` parameter to return either processed data or raw Stripe objects
   - Serializes Stripe timestamps to Python datetimes

3. **Custom Model Managers & QuerySets**: Complex queries encapsulated in managers:
   - `UserSubscriptionQuerySet`: Filter by date ranges, status, user IDs
   - `SubscriptionPriceQuerySet`: Filter by featured, interval, active subscriptions

4. **Environment-Based Configuration**: Uses `python-decouple` for all sensitive data:
   - `config("VAR_NAME", default=value, cast=type)`
   - Never hardcode secrets

## Database Models

### Core Models

#### `Customer` (customers/models.py)
- Links Django User to Stripe Customer
- Auto-creates Stripe customer on email confirmation
- **Fields:** `user` (OneToOne), `stripe_id`, `init_email`, `init_email_confirmed`

#### `Subscription` (subscriptions/models.py)
- Represents subscription plans (Stripe Products)
- **Fields:** `name`, `subtitle`, `active`, `groups`, `permissions`, `stripe_id`, `order`, `featured`, `features`
- Auto-creates Stripe product on save if `stripe_id` is None
- **Methods:** `get_features_as_list()`

#### `SubscriptionPrice` (subscriptions/models.py)
- Represents pricing tiers (Stripe Prices)
- **Fields:** `subscription` (FK), `stripe_id`, `price`, `interval` (MONTHLY/YEARLY), `featured`, `order`
- **IntervalChoices:** `MONTHLY = "month"`, `YEARLY = "year"`
- Auto-creates Stripe price on save

#### `UserSubscription` (subscriptions/models.py)
- Tracks user's active subscription
- **Fields:** `user` (OneToOne), `subscription` (FK), `stripe_id`, `status`, `cancel_at_period_end`, `current_period_start`, `current_period_end`
- **Properties:** `is_active` (checks status == "active" or "trialing")
- **Methods:** 
  - `get_stripe_subscription_data()`: Fetch from Stripe
  - `sync_from_stripe()`: Update local data from Stripe
  - `cancel(at_period_end=True)`: Cancel subscription

#### `AgentTrigger` (ai_agent_gateway/models.py)
- Defines automated agent actions
- **Types:** `prompt` (regex-based), `scheduled` (one-time), `periodic` (recurring)
- **Fields:** `trigger_type`, `prompt_pattern`, `scheduled_time`, `periodic_interval`, `action_payload` (JSON)

### Model Relationships

```
User (Django Auth)
  ↓ OneToOne
Customer
  ↓ via stripe_id
UserSubscription
  ↓ FK
Subscription
  ↓ OneToMany
SubscriptionPrice
```

## Views & URL Patterns

### Authentication Flow
- **Login:** `/login/` → `auth.views.login_view`
- **Register:** `/register/` → `auth.views.register_view`
- **Allauth:** `/accounts/*` → Django Allauth URLs (email verification, social auth)

### Subscription Flow
1. **Browse Plans:** `/pricing/` or `/pricing/<interval>/` → `subscription_price_view`
2. **Select Plan:** `/checkout/sub-price/<price_id>/` → `product_price_redirect_view`
   - Stores `price_id` in session
3. **Start Checkout:** `/checkout/start/` → `checkout_redirect_view`
   - Requires login
   - Creates Stripe checkout session
   - Redirects to Stripe hosted checkout
4. **Finalize:** `/checkout/success/?session_id=<id>` → `checkout_finalize_view`
   - Creates or updates `UserSubscription`
   - Triggers permission/group assignment via signal

### Dashboard & Management
- **Landing:** `/` → `landing_dashboard_page_view` (redirects to dashboard if authenticated)
- **Dashboard:** Internal → `dashboard_view` (requires login)
- **User Subscription:** `/accounts/billing/` → `user_subscription_view`
- **Cancel Subscription:** `/accounts/billing/cancel` → `user_subscription_cancel_view`

### AI Agent Gateway
- **Handle Prompt:** `/prompt/` → `handle_prompt` (POST JSON with `prompt` field)
- **List Triggers:** `/triggers/` → `trigger_list`
- **Create Trigger:** `/triggers/create/` → `create_trigger`

## Helper Modules

### helpers/billing.py
Stripe API wrapper functions:
- `create_customer(name, email, metadata)` → Stripe customer ID
- `create_product(name, metadata)` → Stripe product ID
- `create_price(currency, unit_amount, interval, product)` → Stripe price ID
- `start_checkout_session(customer_stripe_id, success_url, cancel_url, price_stripe_id)` → Checkout URL
- `get_checkout_customer_plan(session_id)` → Extract plan/customer data
- `get_subscription(stripe_id)` → Subscription data
- `cancel_subscription(stripe_id, reason, feedback, cancel_at_period_end)`
- `serialize_subscription_data(subscription_response)` → Format Stripe timestamps

### helpers/numbers.py
- `shorten_number(value)` → Format large numbers (e.g., 1500000 → "1.5M")

### helpers/date_utils.py
- `timestamp_as_datetime(timestamp)` → Convert Unix timestamp to Python datetime

### helpers/downloader.py
- `download_to_local(url, out_path, parent_mkdir=True)` → Download files from URLs

## Custom Management Commands

### `vendor_pull`
**Usage:** `python src/manage.py vendor_pull`
**Purpose:** Downloads vendor static files (Flowbite CSS/JS, SaaS theme) from CDN
**Location:** `src/commando/management/commands/vendor_pull.py`
**Configuration:** `settings.VENDOR_STATICFILES` dict

## Configuration & Environment Variables

### Required Environment Variables (.env file)
```bash
# Django Core
DJANGO_SECRET_KEY=<secret>          # Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_DEBUG=True                   # False in production
BASE_URL=http://127.0.0.1:8000     # Full URL for production

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
CONN_MAX_AGE=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...      # Use sk_live_... in production
STRIPE_TEST_OVERRIDE=False

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Admin (optional)
ADMIN_USER_NAME=Admin Name
ADMIN_USER_EMAIL=admin@example.com
```

### Static Files Configuration
- **Development:** Files served from `src/staticfiles/` and `src/local-cdn/`
- **Production:** WhiteNoise serves compressed static files
- **Vendor Files:** Downloaded to `src/staticfiles/vendors/` via `vendor_pull`
- **Collection:** `python src/manage.py collectstatic` copies to `src/local-cdn/`

## Celery Task System

### Task Definitions (ai_agent_gateway/tasks.py)
1. **`process_agent_action(trigger_id, payload)`**
   - Executes agent action for a trigger
   - Updates `last_triggered` timestamp
   - Called by: prompt handler, scheduled/periodic checkers

2. **`check_scheduled_triggers()`**
   - Runs periodically to find due scheduled triggers
   - Processes all due triggers and clears `scheduled_time`

3. **`check_periodic_triggers()`**
   - Runs periodically to find due periodic triggers
   - Uses `F()` expressions to avoid race conditions
   - Checks if `last_triggered + periodic_interval <= now`

### Celery Configuration (genapp/settings.py)
```python
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

**Note:** Celery is configured but not required for basic functionality. Redis must be running for async tasks.

## Logging Configuration

### Asynchronous Logging Setup
- **Handler:** `QueueHandler` with shared `log_queue` from `genapp/log_listener.py`
- **Formatters:** `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- **Loggers:** `django`, `my_app`, and root logger
- **Output:** Logs written to `logs/application.log` (must create `logs/` directory)

### Logging Best Practices
```python
import logging
logger = logging.getLogger(__name__)

# Info level for normal operations
logger.info(f"User {user.username} logged in")

# Warning for recoverable issues
logger.warning(f"Invalid price_id: {price_id}")

# Error with exception info for failures
try:
    # operation
except Exception as e:
    logger.error(f"Failed to create customer: {e}", exc_info=True)
```

## Testing

### Running Tests
```bash
# All tests
python src/manage.py test

# Specific app
python src/manage.py test subscriptions

# Specific test class
python src/manage.py test subscriptions.tests.SubscriptionTestCase
```

### Test Configuration
- Uses `StaticFilesStorage` instead of WhiteNoise in test mode (see `settings.py`)
- SQLite in-memory database for tests

## Code Style Guidelines

### Imports
```python
# Standard library
import logging
import datetime

# Django core
from django.db import models
from django.conf import settings
from django.shortcuts import render, redirect

# Third-party
import stripe

# Local apps
from subscriptions.models import Subscription
import helpers.billing
```

### View Structure
```python
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

@login_required
def my_view(request):
    """
    Clear docstring explaining the view's purpose.
    
    Args:
        request: The HTTP request.
        
    Returns:
        A rendered HTML response.
    """
    logger.info(f"View accessed by {request.user.username}")
    try:
        # Logic here
        return render(request, "template.html", context)
    except Exception as e:
        logger.error(f"Error in view: {e}", exc_info=True)
        # Handle error
```

### Model Save Override Pattern
```python
def save(self, *args, **kwargs):
    """Save override for custom logic."""
    if not self.stripe_id:
        try:
            logger.info(f"Creating Stripe resource for {self.name}")
            self.stripe_id = create_stripe_resource(self.name)
        except Exception as e:
            logger.error(f"Error creating Stripe resource: {e}", exc_info=True)
    super().save(*args, **kwargs)
```

## Common Patterns & Conventions

### Permission Handling
- **Subscription Permissions:** Defined in `SUBSCRIPTION_PERMISSION` list
- **Groups:** Created automatically: `free-trial`, `default`, `member`
- **Signal-Based:** `user_sub_post_save` syncs user permissions with subscription

### Stripe Data Sync
- **Local → Stripe:** On model save (Customer, Subscription, SubscriptionPrice)
- **Stripe → Local:** Via `sync_from_stripe()` method or `refresh_active_users_subscriptions()` utility

### Session Management
- Store checkout data: `request.session['checkout_subscription_price_id'] = price_id`
- Clear after use: `request.session.pop('key', None)`

### Error Handling
```python
try:
    # Risky operation
    result = stripe_operation()
except SpecificException as e:
    logger.error(f"Specific error: {e}", exc_info=True)
    messages.error(request, "User-friendly message")
    return redirect("fallback_view")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return HttpResponseBadRequest("Generic error message")
```

## Deployment Notes

### Production Checklist
1. Set `DJANGO_DEBUG=False`
2. Configure `BASE_URL` to production domain
3. Update `ALLOWED_HOSTS` in settings.py
4. Set `CSRF_TRUSTED_ORIGINS` for your domain
5. Use production Stripe keys (`sk_live_...`)
6. Configure PostgreSQL via `DATABASE_URL`
7. Set strong `DJANGO_SECRET_KEY`
8. Install dependencies: `pip install -r src/requirements/requirements-prod.txt`
9. Download vendor files: `python src/manage.py vendor_pull`
10. Collect static files: `python src/manage.py collectstatic --noinput`
11. Run migrations: `python src/manage.py migrate`
12. Configure Redis for Celery (if using async features)
13. Start Celery workers: `celery -A genapp worker -l info`
14. Start Celery beat: `celery -A genapp beat -l info`

### Docker Deployment

The Dockerfile is configured to use RAV for production dependency management:

```dockerfile
# Copy RAV automation files
COPY ./rav.py /code/rav.py
COPY ./rav.yaml /code/rav.yaml
COPY ./src/requirements /code/src/requirements

# Install pip-tools and PyYAML for RAV
RUN pip install pip-tools pyyaml

# Use RAV to install production dependencies
RUN python rav.py install-prod
```

**Benefits:**
- Consistent dependency management across development and production
- Uses same RAV tool for both environments
- Automatically installs only production packages
- Ensures requirements are always up-to-date

**Build the Docker image:**
```bash
docker build -t django-saas-platform .
```

**Run the container:**
```bash
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY="your-secret-key" \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e STRIPE_SECRET_KEY="sk_live_..." \
  django-saas-platform
```

**Alternative: Manual requirements installation**
If you prefer not to use RAV in Docker, uncomment the fallback line in Dockerfile:
```dockerfile
RUN pip install -r /code/src/requirements/requirements-prod.txt
```

### WSGI/ASGI
- **WSGI:** `src/genapp/wsgi.py` (for Gunicorn)
- **ASGI:** `src/genapp/asgi.py` (for async support)

### Procfile (Railway/Heroku)
Located at: `src/Procfile`

## Troubleshooting

### Common Issues

1. **Missing .env file**: Create `.env` in project root with required variables
2. **Database URL format**: `postgresql://user:pass@host:port/dbname` (no `psql` prefix)
3. **Missing logs directory**: `mkdir -p logs` in project root
4. **Missing vendor files**: Run `python src/manage.py vendor_pull`
5. **Celery not running**: Optional for basic features, required for agent gateway
6. **Static files 404**: Run `collectstatic` or `vendor_pull`

### Debug Commands
```bash
# Check Python environment
python --version
which python

# Check installed packages
pip list | grep -i django

# Verify migrations
python src/manage.py showmigrations

# Create superuser
python src/manage.py createsuperuser

# Django shell
python src/manage.py shell

# Check for errors
python src/manage.py check
```

## Development Workflow

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   # Using RAV (recommended for development)
   python rav.py setup-dev          # Compile + install dev dependencies
   # Or: python rav.py install-dev   # Install only (if already compiled)
   
   # Using Make (alternative)
   make install-dev
   
   # Manual installation
   pip install -r src/requirements/requirements-prod.txt -r src/requirements/requirements-dev.txt
   ```
   
   **Note:** Use `setup-dev` for development, `setup-prod` for production servers.

3. **Run migrations:**
   ```bash
   python src/manage.py migrate
   ```

4. **Download vendor files:**
   ```bash
   python src/manage.py vendor_pull
   ```

5. **Run development server:**
   ```bash
   python src/manage.py runserver
   ```

6. **Access application:**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Dependency Management

This project uses **pip-tools** for dependency management with **RAV (Requirements Automation & Virtualization)** for task automation. All requirement files are located in `src/requirements/`:

- **requirements-prod.in** - Production dependencies (source of truth)
- **requirements-prod.txt** - Compiled production deps with pinned versions (auto-generated)
- **requirements-dev.in** - Development dependencies (source of truth)
- **requirements-dev.txt** - Compiled dev dependencies (auto-generated)

### RAV Automation Tool

RAV (`rav.py` + `rav.yaml`) automates dependency management tasks and clearly differentiates between development and production environments.

**Development vs Production:**

| Task | Production | Development |
|------|-----------|-------------|
| Install only | `install-prod` | `install-dev` |
| Compile + Install | `setup-prod` | `setup-dev` |
| Full bootstrap | `bootstrap-prod` | `bootstrap-dev` |

**Production Environment (Production Server):**
```bash
python rav.py install-prod        # Install production dependencies only
python rav.py setup-prod          # Compile + install production
python rav.py bootstrap-prod      # Create venv + setup production
```
- Installs only `requirements-prod.txt`
- No testing tools (hypothesis)
- No pip-tools in final environment
- Minimal dependencies for production

**Development Environment (Local Machine):**
```bash
python rav.py install-dev         # Install dev + production dependencies
python rav.py setup-dev           # Compile + install both dev and prod
python rav.py bootstrap-dev       # Create venv + setup development
```
- Installs both `requirements-prod.txt` AND `requirements-dev.txt`
- Includes testing tools (hypothesis)
- Includes pip-tools for dependency management
- All tools needed for development

**Common Commands (Both Environments):**
```bash
python rav.py --list              # List all available tasks
python rav.py --help              # Show help information
python rav.py compile             # Compile both requirements files
python rav.py upgrade             # Upgrade all dependencies to latest
python rav.py sync                # Sync environment with requirements
python rav.py create-venv         # Create a new virtual environment
```

**Configuration:** All tasks are defined in `rav.yaml` in the project root.

**Example Workflows:**
```bash
# Local development setup
python rav.py bootstrap-dev
python src/manage.py migrate
python src/manage.py runserver

# Production deployment
python rav.py bootstrap-prod
python src/manage.py migrate
gunicorn genapp.wsgi:application
```

### Managing Dependencies

**Add a new dependency:**
```bash
# For production
echo "package-name>=1.0" >> src/requirements/requirements-prod.in

# For development only
echo "dev-package>=1.0" >> src/requirements/requirements-dev.in

# Recompile
python rav.py compile
# Or: make compile
```

**Update all dependencies:**
```bash
python rav.py upgrade
# Or: make upgrade
```

**Sync environment with requirements:**
```bash
python rav.py sync
# Or: make sync
```

### Key Dependencies

- **django>=5.0,<5.2** - Web framework
- **stripe** - Payment processing
- **django-allauth[socialaccount]** - Authentication with social login
- **celery** - Async task queue
- **redis** - Message broker for Celery
- **django-celery-beat** - Periodic task scheduler
- **whitenoise** - Static file serving
- **psycopg[binary]** - PostgreSQL adapter
- **dj-database-url** - Database URL parsing
- **python-decouple** - Environment variable management
- **gunicorn** - WSGI HTTP server for production
- **pip-tools** - Dependency management (dev only)

## Important Notes for Copilot

1. **Always use logging instead of print statements**
2. **Never hardcode secrets - use `config()` from decouple**
3. **Use RAV for dependency management - `python rav.py setup-dev` for development, `python rav.py setup-prod` for production**
4. **All Stripe operations should go through `helpers/billing.py`**
4. **Signal handlers should be lightweight - delegate heavy work to tasks**
5. **Use try/except blocks with specific exceptions when possible**
6. **Include `exc_info=True` in error logs for full traceback**
7. **Views should return user-friendly error messages**
8. **Models should auto-create Stripe resources on first save**
9. **QuerySets should be filtered in custom managers, not views**
10. **Templates inherit from `base.html` or app-specific base templates**
11. **Static files go in `src/staticfiles/`, not `src/static/`**
12. **Management commands go in `src/commando/management/commands/`**
13. **Use `@login_required` for authenticated views**
14. **Check subscription permissions with `request.user.has_perm('subscriptions.pro')`**
15. **Time-based queries use timezone-aware datetimes**

## Quick Reference

### Create a new app
```bash
cd src
python manage.py startapp myapp
```

### Add to INSTALLED_APPS in settings.py
```python
INSTALLED_APPS = [
    # ... existing apps
    'myapp',
]
```

### Create a model
```python
from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

### Create a view
```python
from django.shortcuts import render

def my_view(request):
    return render(request, 'myapp/template.html', {})
```

### Add URL pattern
```python
# In src/genapp/urls.py
from myapp import views as myapp_views

urlpatterns = [
    # ...
    path('mypath/', myapp_views.my_view, name='my_view'),
]
```

---

**Last Updated:** December 16, 2025
**Django Version:** 5.1.15
**Python Version:** 3.13.0+
