import logging
"""
This module contains the views for the dashboard app.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

logger = logging.getLogger(__name__)

# Create your views here.
@login_required
def dashboard_view(request):
    """
    Renders the main dashboard page for authenticated users.

    Args:
        request: The HTTP request.

    Returns:
        A rendered HTML response.
    """
    logger.info(f"Dashboard accessed by user: {request.user.username}")
    return render(request, "dashboard/main.html", {})