from django.shortcuts import render
from subscriptions.models import SubscriptionPrice
from django.urls import reverse

# Create your views here.
def subscription_price_view(request, interval="month"):
    ''' This method handles the logic required for Pricing'''

    # Build query set, which is filtered by featured
    qs = SubscriptionPrice.objects.filter(featured=True)

    # Define variables for interval choices provided
    inv_mo = SubscriptionPrice.IntervalChoices.MONTHLY
    inv_yr = SubscriptionPrice.IntervalChoices.YEARLY

    # Further filter the query set by interval.
    object_list=qs.filter(interval=inv_mo)
    url_path_name = "pricing_interval"

    # Define the url for the interval choices.
    mo_url = reverse(url_path_name, kwargs={"interval": inv_mo})
    yr_url = reverse(url_path_name, kwargs={"interval": inv_yr})

    # Set the default active tab to monthly
    active = inv_mo

    # Based on the interval tab selection change the query set to yearly.
    if interval == inv_yr:
        active = inv_yr
        object_list = qs.filter(interval=inv_yr)

    return render(request, "subscriptions/pricing.html", {
        "object_list":object_list,
        "mo_url":mo_url,
        "yr_url":yr_url,
        "active":active,
    })
