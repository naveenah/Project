"""
This module contains the views for the subscriptions app.
"""
import helpers.billing
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from subscriptions.models import SubscriptionPrice, UserSubscription
from subscriptions import utils as subs_utils

# Create your views here.
@login_required
def user_subscription_view(request):
    """
    Renders the user's subscription details page.

    On POST, it refreshes the user's subscription data from Stripe.

    Args:
        request: The HTTP request.

    Returns:
        A rendered HTML response.
    """
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    if request.method == "POST":
        finished = subs_utils.refresh_active_users_subscriptions(user_ids=[request.user.id],active_only=False)
        if finished:
            messages.success(request, "Your plan details have been refreshed ")
        else:
            messages.error(request, "Your plan details have not been refreshed, please try again ")
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_detail_view.html', {"subscription" : user_sub_obj})

@login_required
def user_subscription_cancel_view(request):
    """
    Renders the subscription cancellation page.

    On POST, it cancels the user's subscription in Stripe.

    Args:
        request: The HTTP request.

    Returns:
        A rendered HTML response.
    """
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    if request.method == "POST":
        if user_sub_obj.stripe_id:    
            sub_data = helpers.billing.cancel_subscription(user_sub_obj.stripe_id,
                                                           reason="User wanted to end", 
                                                           feedback="other",
                                                           cancel_at_period_end=True,
                                                           raw=False)
            for k,v in sub_data.items():
                setattr(user_sub_obj,k,v)
            user_sub_obj.save()
            messages.success(request, "Your plan has been cancelled")
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_cancel_view.html', {"subscription" : user_sub_obj})

def subscription_price_view(request, interval="month"):
    """
    Renders the pricing page, showing subscription prices for a given interval.

    Args:
        request: The HTTP request.
        interval (str): The billing interval to display ("month" or "year").

    Returns:
        A rendered HTML response.
    """

    # Build query set, which is filtered by featured
    qs = SubscriptionPrice.objects.filter(featured=True)

    # Define variables for interval choices provided
    inv_mo = SubscriptionPrice.IntervalChoices.MONTHLY
    inv_yr = SubscriptionPrice.IntervalChoices.YEARLY

    # Further filter the query set by interval.
    object_list = qs.filter(subscription__active=True, interval=inv_mo)
    url_path_name = "pricing_interval"

    # Define the url for the interval choices.
    mo_url = reverse(url_path_name, kwargs={"interval": inv_mo})
    yr_url = reverse(url_path_name, kwargs={"interval": inv_yr})

    # Set the default active tab to monthly
    active = inv_mo

    # Based on the interval tab selection change the query set to yearly.
    if interval == inv_yr:
        active = inv_yr
        object_list = qs.filter(subscription__active=True, interval=inv_yr)

    return render(request, "subscriptions/pricing.html", {
        "object_list":object_list,
        "mo_url":mo_url,
        "yr_url":yr_url,
        "active":active,
    })
