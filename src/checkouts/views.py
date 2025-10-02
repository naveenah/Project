import logging
import helpers.billing
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from subscriptions.models import SubscriptionPrice, Subscription, UserSubscription
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest

User = get_user_model()
BASE_URL = settings.BASE_URL
logger = logging.getLogger(__name__)

# Create your views here.
def product_price_redirect_view(request, price_id=None, *args, **kwargs):
    """
    Redirects to the checkout start page with the selected price ID stored in the session.
    """
    logger.info(f"product_price_redirect_view started for price_id: {price_id}")
    try:
        price_obj = get_object_or_404(SubscriptionPrice, id=price_id)
        request.session['checkout_subscription_price_id'] = price_obj.id
        logger.info(f"Set checkout_subscription_price_id to {price_obj.id} in session.")
        return redirect("stripe-checkout-start")
    except Exception as e:
        logger.error(f"Error in product_price_redirect_view for price_id {price_id}: {e}", exc_info=True)
        messages.error(request, "There was an error with your selection.")
        return redirect("pricing")

@login_required
def checkout_redirect_view(request):
    """
    Redirects the user to the Stripe checkout page for the selected subscription price.
    """
    checkout_subscription_price_id = request.session.get("checkout_subscription_price_id")
    logger.info(f"checkout_redirect_view started for user {request.user.username} with price_id {checkout_subscription_price_id}")
    try:
        obj = SubscriptionPrice.objects.get(id=checkout_subscription_price_id)
    except SubscriptionPrice.DoesNotExist:
        logger.warning(f"SubscriptionPrice with id {checkout_subscription_price_id} not found for user {request.user.username}.")
        obj = None

    if checkout_subscription_price_id is None or obj is None:
        logger.warning(f"User {request.user.username} redirected to pricing page due to missing checkout_subscription_price_id or price object.")
        return redirect("pricing")
    
    try:
        customer_stripe_id = request.user.customer.stripe_id
        success_url_path = reverse("stripe-checkout-end")
        pricing_url_path = reverse("pricing")
        success_url = f"{BASE_URL}{success_url_path}"
        cancel_url = f"{BASE_URL}{pricing_url_path}"
        price_stripe_id = obj.stripe_id

        logger.info(f"Initiating Stripe checkout session for user {request.user.username} with price {price_stripe_id}.")
        url = helpers.billing.start_checkout_session(
            customer_stripe_id,
            success_url=success_url,
            cancel_url=cancel_url,
            price_stripe_id=price_stripe_id,
            raw=False
        )
        return redirect(url)
    except Exception as e:
        logger.error(f"Error processing checkout for user {request.user.username}: {e}", exc_info=True)
        messages.error(request, "There was an error processing your checkout.")
        return redirect("pricing")

def checkout_finalize_view(request):
    """
    Finalizes the checkout process after a successful payment with Stripe.
    Creates or updates the user's subscription.
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        session_id = request.session.get('checkout_session_id')

    logger.info(f"checkout_finalize_view started with session_id: {session_id}")
    if not session_id:
        logger.warning("checkout_finalize_view called without a session_id.")
        return HttpResponseBadRequest("Session ID is required.")
        
    try:
        checkout_data = helpers.billing.get_checkout_customer_plan(session_id)
        plan_id = checkout_data.pop('plan_id')
        customer_id = checkout_data.pop('customer_id')
        sub_stripe_id = checkout_data.pop('sub_stripe_id')
        subscription_data = {**checkout_data}
        logger.info(f"Processing checkout for plan_id: {plan_id}, customer_id: {customer_id}")
    
        try:
            sub_obj = Subscription.objects.get(subscriptionprice__stripe_id = plan_id)
        except Subscription.DoesNotExist:
            logger.error(f"Subscription not found for plan_id: {plan_id}")
            sub_obj=None

        try:
            user_obj = User.objects.get(customer__stripe_id = customer_id)
        except User.DoesNotExist:
            logger.error(f"User not found for customer_id: {customer_id}")
            user_obj=None
        _user_sub_exist = False
        updated_sub_options = {
            "subscription": sub_obj,
            "stripe_id": sub_stripe_id,
            "user_cancelled": False,
            **subscription_data,
        }
        try:
            _user_sub_obj = UserSubscription.objects.get(user = user_obj)
            _user_sub_exist = True
        except UserSubscription.DoesNotExist:            
            _user_sub_obj = UserSubscription.objects.create(
                user=user_obj, 
                **updated_sub_options,
                )
        except:
            _user_sub_obj = None

        if None in [sub_obj, user_obj, _user_sub_obj]:
            return HttpResponseBadRequest(
                "There was an error with your account please contact us.")
        
        if _user_sub_exist:
            for key, value in updated_sub_options.items():
                setattr(_user_sub_obj, key, value)
            _user_sub_obj.save()
            logger.info(f"Updated subscription for user {user_obj.username}.")
        else:
            logger.info(f"Created new subscription for user {user_obj.username}.")
        
        messages.success(request, "Your subscription has been updated.")
        return redirect("user_subscription")
    except Exception as e:
        logger.error(f"Error finalizing checkout for session_id {session_id}: {e}", exc_info=True)
        messages.error(request, "There was an error finalizing your checkout.")
        return redirect("pricing")