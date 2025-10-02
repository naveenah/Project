import logging
"""
This module contains the views for the profiles app.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

@login_required
def profile_list_view(request):
    """
    Renders a list of active user profiles.

    Args:
        request: The HTTP request.

    Returns:
        A rendered HTML response.
    """
    logger.info(f"Profile list view accessed by: {request.user.username}")
    context = {
        "object_list": User.objects.filter(is_active=True)
    }
    return render(request, "profiles/list.html", context)

@login_required
def profile_detail_view(request,username=None, *args, **kwargs):
    """
    Renders the detail view for a single user profile.

    Args:
        request: The HTTP request.
        username (str): The username of the profile to view.

    Returns:
        A rendered HTML response.
    """
    logger.info(f"Profile detail view for '{username}' accessed by: {request.user.username}")
    user = request.user
    profile_user_object = get_object_or_404(User,username=username)
    is_me = profile_user_object == user
    if is_me:
        logger.info(f"User {request.user.username} is viewing their own profile.")
    else:
        logger.info(f"User {request.user.username} is viewing the profile of {username}.")
    context = {
        "object": profile_user_object,
        "instance": profile_user_object,
        "owner": is_me,
    }
    return render(request, "profiles/detail.html", context)
