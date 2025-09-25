"""
This module contains utility functions for the subscriptions app.
"""
import helpers.billing
from django.db.models import Q
from customers.models import Customer
from subscriptions.models import Subscription, UserSubscription, SubscriptionStatus

def refresh_active_users_subscriptions(
        user_ids=None, 
        active_only=True,
        days_left=-1,
        days_ago=-1,
        day_start=-1,
        day_end=-1,
        verbose=False):
    """
    Refreshes the subscription data for active users from Stripe.

    Args:
        user_ids (list): A list of user IDs to refresh.
        active_only (bool): If True, only refreshes active and trialing
            subscriptions.
        days_left (int): Filters subscriptions by the number of days left.
        days_ago (int): Filters subscriptions by the number of days ago they
            were created.
        day_start (int): The start of the date range to filter by.
        day_end (int): The end of the date range to filter by.
        verbose (bool): If True, prints progress information.

    Returns:
        True if all subscriptions were refreshed successfully, False otherwise.
    """
    
    qs = UserSubscription.objects.all()

    if active_only:
        qs = qs.by_active_trialing()
    if user_ids is not None:
        qs = qs.by_user_ids(user_ids=user_ids)
    if days_ago > -1:
        qs = qs.by_days_ago(days_ago=days_ago)
    if days_left > -1:
        qs = qs.by_days_left(days_left=days_left)
    if day_start > -1 and day_end > -1:
        qs = qs.by_range(days_start=day_start, days_end=day_end, verbose=verbose)

    complete_count = 0
    qs_count = qs.count()
    for obj in qs:
        if verbose:
            print("updating user", obj.user, obj.subscription, obj.current_period_end)
        if obj.stripe_id:    
            sub_data = helpers.billing.get_subscription(obj.stripe_id, raw=False)
            for k,v in sub_data.items():
                setattr(obj,k,v)
            obj.save()
            complete_count += 1
    return complete_count == qs_count

def clear_dangling_subs():
    """
    Cancels any active Stripe subscriptions that do not have a corresponding
    UserSubscription object in the database.
    """
    qs = Customer.objects.filter(stripe_id__isnull=False)
    for customer_obj in qs:
        user = customer_obj.user
        customer_stripe_id = customer_obj.stripe_id
        print(f"Sync {user} - {customer_stripe_id} subs and remove old ones")
        subs = helpers.billing.get_customer_active_subscriptions(customer_stripe_id)
        for sub in subs:
            existing_user_subs_qs = UserSubscription.objects.filter(stripe_id__iexact=f"{sub.id}.strip()")
            if existing_user_subs_qs.exists():
                continue
            helpers.billing.cancel_subscription(
                sub.id, 
                reason="Cancel dangling subscriptions", 
                cancel_at_period_end=False)
            print(sub.id, existing_user_subs_qs.exists())

def sync_subs_group_permissions(): 
    """
    Syncs the permissions of subscription groups with the permissions of their
    associated subscriptions.
    """
    qs = Subscription.objects.filter(active=True)
    for obj in qs:
        sub_perms = obj.permissions.all()
        for group in obj.groups.all():
            group.permissions.set(sub_perms)




