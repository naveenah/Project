import logging
"""
This module provides helper functions for interacting with the Stripe API.

It includes functions for creating customers, products, and prices, as well as
managing subscriptions and checkout sessions.
"""
# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
import stripe
from decouple import config
from . import date_utils

logger = logging.getLogger(__name__)

DJANGO_DEBUG=config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY=config("STRIPE_SECRET_KEY", default="", cast=str)
STRIPE_TEST_OVERRIDE=config("STRIPE_TEST_OVERRIDE", default=False, cast=bool)

#if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG and not STRIPE_TEST_OVERRIDE:
#    raise ValueError("Invalid stripe key in Production")

stripe.api_key = STRIPE_SECRET_KEY
logger.info("Stripe API key set.")

def serialize_subscription_data(subscription_response):
    """
    Serializes a Stripe subscription object into a dictionary.

    Args:
        subscription_response: A Stripe subscription object.

    Returns:
        A dictionary containing the subscription's status, current period start
        and end dates, and whether it will be canceled at the period end.
    """
    status = subscription_response.status
    current_period_start = date_utils.timestamp_as_datetime(subscription_response.current_period_start)
    current_period_end = date_utils.timestamp_as_datetime(subscription_response.current_period_end)
    cancel_at_period_end = subscription_response.cancel_at_period_end
    data = {
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "status" : status,
        "cancel_at_period_end": cancel_at_period_end,
    }
    logger.debug(f"Serialized subscription data: {data}")
    return data

def create_customer(
        name = "",
        email= "",
        metadata={},
        raw = False):
    """
    Creates a new customer in Stripe.

    Args:
        name (str): The customer's name.
        email (str): The customer's email address.
        metadata (dict): A dictionary of metadata to associate with the customer.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        The Stripe customer ID, or the raw response if `raw` is True.
    """
    logger.info(f"Creating Stripe customer with email: {email}")
    try:
        response = stripe.Customer.create(name=name, email=email, metadata=metadata,)
        if raw:
            logger.debug("Returning raw Stripe customer response.")
            return response
        
        stripe_id = response.id
        logger.info(f"Stripe customer created with ID: {stripe_id}")
        return stripe_id
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {e}", exc_info=True)
        raise
    #stripe.api_key = STRIPE_SECRET_KEY
    #stripe.Customer.create(
    #  name="Jenny Rosen",
    #  email="jennyrosen@example.com",
    #)

def create_product(name = "",
        metadata={},
        raw = False):
    """
    Creates a new product in Stripe.

    Args:
        name (str): The product's name.
        metadata (dict): A dictionary of metadata to associate with the product.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        The Stripe product ID, or the raw response if `raw` is True.
    """
    logger.info(f"Creating Stripe product with name: {name}")
    try:
        response = stripe.Product.create(
            name=name, 
            metadata=metadata,
            )
        if raw:
            logger.debug("Returning raw Stripe product response.")
            return response
        
        stripe_id = response.id
        logger.info(f"Stripe product created with ID: {stripe_id}")
        return stripe_id
    except Exception as e:
        logger.error(f"Error creating Stripe product: {e}", exc_info=True)
        raise

def create_price(currency="usd",
                unit_amount="9999",
                interval="month",
                product=None,
                metadata={},
                raw = False):
    """
    Creates a new price in Stripe.

    Args:
        currency (str): The currency of the price.
        unit_amount (str): The amount of the price in cents.
        interval (str): The billing interval ('month', 'year', etc.).
        product (str): The Stripe product ID.
        metadata (dict): A dictionary of metadata to associate with the price.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        The Stripe price ID, or the raw response if `raw` is True.
    """
    if product is None:
        raise ValueError("Stripe `product` ID is required.")
    logger.info(f"Creating Stripe price for product: {product}")
    try:
        response = stripe.Price.create(
            currency=currency,
            unit_amount=unit_amount,
            recurring={"interval": interval},
            product=product,
            metadata=metadata,
        )
        if raw:
            logger.debug("Returning raw Stripe price response.")
            return response
        stripe_id = response.id
        logger.info(f"Stripe price created with ID: {stripe_id}")
        return stripe_id
    except Exception as e:
        logger.error(f"Error creating Stripe price: {e}", exc_info=True)
        raise

def start_checkout_session(customer_stripe_id,
                           success_url="",
                           cancel_url="",
                           price_stripe_id="",
                           raw=False):
    """
    Starts a new checkout session in Stripe.

    Args:
        customer_stripe_id (str): The customer's Stripe ID.
        success_url (str): The URL to redirect to on successful payment.
        cancel_url (str): The URL to redirect to on canceled payment.
        price_stripe_id (str): The Stripe price ID.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        The checkout session URL, or the raw response if `raw` is True.
    """
    if success_url == "" or cancel_url == "":
        raise ValueError("`success_url` and `cancel_url` are required.")
    logger.info(f"Starting checkout session for customer: {customer_stripe_id} with price: {price_stripe_id}")
    success_url = f'{success_url}?session_id={{CHECKOUT_SESSION_ID}}'
    try:
        response = stripe.checkout.Session.create(
            customer=customer_stripe_id,
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=[
                {"price": price_stripe_id, "quantity": 1},
            ],
            mode="subscription",
        )
        if raw:
            logger.debug("Returning raw Stripe checkout session response.")
            return response
        return response.url
    except Exception as e:
        logger.error(f"Error starting checkout session for customer {customer_stripe_id}: {e}", exc_info=True)
        raise

def get_checkout_session(stripe_id, raw=True):
    """
    Retrieves a checkout session from Stripe.

    Args:
        stripe_id (str): The ID of the checkout session.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        The checkout session URL, or the raw response if `raw` is True.
    """
    response = stripe.checkout.Session.retrieve(
        stripe_id,
        )

    if raw:
        return response
    return response.url 

def get_subscription(stripe_id, raw=True):
    """
    Retrieves a subscription from Stripe.

    Args:
        stripe_id (str): The ID of the subscription.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        A serialized subscription dictionary, or the raw response if `raw` is True.
    """
    response = stripe.Subscription.retrieve(
        stripe_id,
        )

    if raw:
        return response
    return serialize_subscription_data(response) 

def get_customer_active_subscriptions(customer_stripe_id):
    """
    Retrieves all active subscriptions for a customer.

    Args:
        customer_stripe_id (str): The ID of the customer.

    Returns:
        A list of active subscriptions.
    """
    response = stripe.Subscription.list(
        customer=customer_stripe_id,
        status="active"
        )
    return response
    

def cancel_subscription(stripe_id, reason = "", cancel_at_period_end = False,
                        feedback="other", raw=True):
    """
    Cancels a subscription in Stripe.

    Args:
        stripe_id (str): The ID of the subscription to cancel.
        reason (str): The reason for cancellation.
        cancel_at_period_end (bool): If True, cancels the subscription at the
            end of the current billing period.
        feedback (str): Customer feedback on the cancellation.
        raw (bool): If True, returns the raw Stripe API response.

    Returns:
        A serialized subscription dictionary, or the raw response if `raw` is True.
    """

    if cancel_at_period_end:
        response = stripe.Subscription.modify(
            stripe_id,
            cancel_at_period_end=cancel_at_period_end,
            cancellation_details={
                "comment": reason,
                "feedback": feedback,
            }
            )
    else:
        response = stripe.Subscription.cancel(
            stripe_id,
            cancellation_details={
                "comment": reason,
                "feedback": feedback,
            }
            )

    if raw:
        return response
    return serialize_subscription_data(response) 

def get_checkout_customer_plan(session_id):
    """
    Retrieves customer and plan information from a checkout session.

    Args:
        session_id (str): The ID of the checkout session.

    Returns:
        A dictionary containing customer and plan information.
    """
    checkout_r = get_checkout_session(session_id,raw=True)
    customer_id = checkout_r.customer
    sub_stripe_id = checkout_r.subscription
    sub_r = get_subscription(sub_stripe_id,raw=True)
    # current_period_start
    # current_period_end
    sub_plan = sub_r.plan
    subscription_data = serialize_subscription_data(sub_r)
    
    data = {
        "customer_id": customer_id,
        "plan_id": sub_plan.id,
        "sub_stripe_id": sub_stripe_id,
        **subscription_data,
    }
    return data