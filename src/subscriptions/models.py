import logging
"""
This module contains the models for the subscriptions app.
"""
import datetime
import helpers.billing
from django.db.models import Q
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils import timezone
import stripe

User = settings.AUTH_USER_MODEL
ALLOW_CUSTOM_GROUPS=True
logger = logging.getLogger(__name__)

SUBSCRIPTION_PERMISSION = [
    ("advanced", "Advanced Perm"), # subscriptions.advanced
    ("pro", "Pro Perm"), # subscriptions.pro
    ("basic", "Basic Perm"), # subscriptions.basic
    ("basic_ai", "Basic AI Perm")
    ]

# Create your models here.
class Subscription(models.Model):
    """
    Represents a subscription plan, equivalent to a Stripe Product.

    Attributes:
        name (str): The name of the subscription.
        subtitle (str): A short description of the subscription.
        active (bool): Whether the subscription is currently active.
        groups (ManyToManyField): The user groups associated with this subscription.
        permissions (ManyToManyField): The permissions associated with this subscription.
        stripe_id (str): The corresponding Stripe Product ID.
        order (int): The display order on the pricing page.
        featured (bool): Whether the subscription is featured on the pricing page.
        updated (DateTimeField): The last time the subscription was updated.
        timestamp (DateTimeField): The time the subscription was created.
        features (str): A newline-separated list of features for this subscription.
    """
    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(Permission, 
    limit_choices_to={
        "content_type__app_label":"subscriptions",
        "codename__in":[x[0]for x in SUBSCRIPTION_PERMISSION]
        }
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    order = models.IntegerField(default=-1, help_text='Ordering on django pricing page')
    featured = models.BooleanField(default=True, help_text = 'Featured on django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    features = models.TextField(help_text="Pricing seperated by new line",blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        permissions= SUBSCRIPTION_PERMISSION
        ordering = ['order', 'featured','-updated']

    def get_features_as_list(self):
        """
        Returns the features of the subscription as a list of strings.
        """
        if not self.features:
            return []
        return [x.strip() for x in self.features.splitlines() if x.strip()]

    def save(self, *args, **kwargs):
        """
        Saves the subscription and creates a corresponding Stripe Product if one
        does not already exist.
        """
        if not self.stripe_id:
            logger.info(f"Creating Stripe product for subscription: {self.name}")
            try:
                stripe_id = helpers.billing.create_product(
                    name=self.name,
                    metadata={
                            "subscription_plan_id":self.id,
                            },
                            raw=False
                        )
                self.stripe_id = stripe_id
                logger.info(f"Stripe product created for subscription {self.name} with stripe_id: {stripe_id}")
            except Exception as e:
                logger.error(f"Error creating Stripe product for subscription {self.name}: {e}", exc_info=True)
        super().save(*args, **kwargs)

class SubscriptionPrice(models.Model):
    """
    Represents the price of a subscription plan, equivalent to a Stripe Price.

    Attributes:
        subscription (ForeignKey): The subscription this price belongs to.
        stripe_id (str): The corresponding Stripe Price ID.
        interval (str): The billing interval (e.g., "month", "year").
        price (Decimal): The price of the subscription.
        order (int): The display order on the pricing page.
        featured (bool): Whether the price is featured on the pricing page.
        updated (DateTimeField): The last time the price was updated.
        timestamp (DateTimeField): The time the price was created.
    """
    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        YEARLY = "year", "Yearly" 

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(max_length=120, 
                                default=IntervalChoices.MONTHLY,
                                choices=IntervalChoices.choices,
                                )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)
    order = models.IntegerField(default=-1, help_text='Ordering on django pricing page')
    featured = models.BooleanField(default=True, help_text = 'Featured on django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def get_price_display(self):
        """
        Returns the price as a formatted string (e.g., "$99.99").
        """
        return self.price / 100

    def __str__(self):
        return f"{self.subscription.name} - {self.interval} - {self.price}"

    class Meta:
        ordering = ['subscription__order', 'order', 'featured','-updated']

    def get_checkout_url(self):
        return reverse("sub-price-checkout", kwargs={"price_id": self.id})

    @property
    def display_sub_name(self):
        return self.subscription.name

    @property
    def display_sub_subtitle(self):
        return self.subscription.subtitle

    @property
    def display_features_list(self):
        return self.subscription.get_features_as_list()

    def save(self, *args, **kwargs):
        """
        Saves the price and creates a corresponding Stripe Price if one does not
        already exist.
        """
        if not self.stripe_id:
            logger.info(f"Creating Stripe price for subscription: {self.subscription.name}")
            try:
                stripe_id = helpers.billing.create_price(
                    currency="usd",
                    unit_amount=self.price,
                    interval=self.interval,
                    product=self.subscription.stripe_id,
                    metadata={
                        "subscription_plan_price_id": self.id
                    },
                    raw=False
                )
                self.stripe_id = stripe_id
                logger.info(f"Stripe price created for subscription {self.subscription.name} with stripe_id: {stripe_id}")
            except Exception as e:
                logger.error(f"Error creating Stripe price for subscription {self.subscription.name}: {e}", exc_info=True)
        super().save(*args, **kwargs)

class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'ACTIVE'
        TRIALING = 'trialing', 'TRIALING'
        INCOMPLETE = 'incomplete','INCOMPLETE'
        INCOMPLETE_EXPIRED = 'incomplete_expired', 'INCOMPLETE_EXPIRED'
        PAST_DUE = 'past_due','PAST_DUE'
        CANCELLED = 'cancelled','CANCELLED'
        UNPAID = 'unpaid','UNPAID'
        PAUSED = 'paused','PAUSED'

class UserSubscriptionQuerySet(models.QuerySet):
    def by_range(self, days_start=7, days_end=120, verbose=True):
        now = timezone.now()
        days_start_from_now = now + datetime.timedelta(days=days_start)
        days_end_from_now = now + datetime.timedelta(days=days_end)
        day_start = days_start_from_now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = days_end_from_now.replace(hour=23, minute=59, second=59, microsecond=59)
        if verbose:
            print(f"Range is {day_start} to {day_end}")
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end
        )
    
    def by_days_left(self, days_left=7):
        now = timezone.now()
        in_n_days = now + datetime.timedelta(days=days_left)
        day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end
        )
    
    def by_days_ago(self, days_ago=3):
        now = timezone.now()
        in_n_days = now - datetime.timedelta(days=days_ago)
        day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end
        )

    def by_active_trialing(self):
        active_qs_lookup = (
            Q(status = SubscriptionStatus.ACTIVE) | 
            Q(status = SubscriptionStatus.TRIALING)
        )
        return self.filter(active_qs_lookup)
    
    def by_user_ids(self, user_ids=None):
        qs = self
        if isinstance(user_ids,list):
            qs = self.filter(user_id__in=user_ids)
        elif isinstance(user_ids, int):
            qs = self.filter(user_ids__in=[user_ids])
        elif isinstance(user_ids, str):
            qs = self.filter(user_ids__in=[user_ids])
        return qs    

class UserSubscriptionManager(models.Manager):
    def get_queryset(self):
        return UserSubscriptionQuerySet(self.model, using=self._db) 

class UserSubscription(models.Model):
    """
    Represents a user's subscription to a subscription plan.

    Attributes:
        user (OneToOneField): The user this subscription belongs to.
        subscription (ForeignKey): The subscription plan.
        stripe_id (str): The corresponding Stripe Subscription ID.
        status (str): The status of the subscription.
        cancel_at_period_end (bool): Whether the subscription will be canceled
            at the end of the current billing period.
        original_period_start (DateTimeField): The start of the original
            billing period.
        current_period_start (DateTimeField): The start of the current
            billing period.
        current_period_end (DateTimeField): The end of the current billing
            period.
        updated (DateTimeField): The last time the subscription was updated.
        timestamp (DateTimeField): The time the subscription was created.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    status = models.CharField(max_length=120, null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_end = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.subscription.name}"

    def get_absolute_url(self):
        return reverse('user_subscription')

    @property
    def is_active(self):
        """
        Returns True if the subscription is active, False otherwise.
        """
        return self.status == "active" or self.status == "trialing"

    def get_stripe_subscription_data(self):
        """
        Retrieves the subscription data from Stripe.
        """
        if not self.stripe_id:
            return None
        logger.info(f"Getting Stripe subscription data for user: {self.user.username}")
        try:
            return helpers.billing.get_customer_active_subscription(
                customer_stripe_id=self.user.customer.stripe_id,
                raw=True
            )
        except Exception as e:
            logger.error(f"Error getting Stripe subscription data for user {self.user.username}: {e}", exc_info=True)
            return None

    def sync_from_stripe(self):
        """
        Syncs the local subscription data with the data from Stripe.
        """
        if not self.stripe_id:
            return
        logger.info(f"Syncing subscription from Stripe for user: {self.user.username}")
        try:
            sub_data = self.get_stripe_subscription_data()
            if sub_data:
                current_period_start = sub_data.get('current_period_start')
                current_period_end = sub_data.get('current_period_end')
                status = sub_data.get('status')
                cancel_at_period_end = sub_data.get('cancel_at_period_end')
                plan_id = sub_data.get('plan', {}).get('id')
                
                self.status = status
                self.current_period_start = datetime.datetime.fromtimestamp(current_period_start, tz=datetime.timezone.utc)
                self.current_period_end = datetime.datetime.fromtimestamp(current_period_end, tz=datetime.timezone.utc)
                self.cancel_at_period_end = cancel_at_period_end
                
                try:
                    sub_price_obj = SubscriptionPrice.objects.get(stripe_id=plan_id)
                    self.subscription = sub_price_obj.subscription
                    logger.info(f"Subscription for user {self.user.username} updated to {self.subscription.name}")
                except SubscriptionPrice.DoesNotExist:
                    logger.warning(f"SubscriptionPrice with stripe_id {plan_id} not found for user {self.user.username}")
                
                self.save()
                logger.info(f"Subscription for user {self.user.username} synced from Stripe.")
        except Exception as e:
            logger.error(f"Error syncing subscription from Stripe for user {self.user.username}: {e}", exc_info=True)

    def cancel(self, at_period_end=True):
        """
        Cancels the subscription in Stripe.

        Args:
            at_period_end (bool): If True, the subscription will be canceled at
                the end of the current billing period. Otherwise, it will be
                canceled immediately.
        """
        if not self.stripe_id:
            return
        logger.info(f"Canceling subscription for user: {self.user.username}")
        try:
            sub_obj = stripe.Subscription.retrieve(self.stripe_id)
            if at_period_end:
                canceled_sub = sub_obj.delete(at_period_end=True)
                self.cancel_at_period_end = canceled_sub.cancel_at_period_end
                self.save()
                logger.info(f"Subscription for user {self.user.username} scheduled for cancellation at period end.")
            else:
                canceled_sub = sub_obj.cancel()
                self.status = canceled_sub.status
                self.save()
                logger.info(f"Subscription for user {self.user.username} canceled immediately.")
        except Exception as e:
            logger.error(f"Error canceling subscription for user {self.user.username}: {e}", exc_info=True)

def user_sub_post_save(sender, instance, created, *args, **kwargs):
    """
    A post-save signal handler for the UserSubscription model.

    When a UserSubscription is created or updated, this function ensures that
    the user's group and permissions are updated to match the subscription.
    """
    user_sub_obj = instance
    if not user_sub_obj.is_active:
        return
    user = user_sub_obj.user
    sub_obj = user_sub_obj.subscription
    
    current_groups = list(user.groups.all())
    current_permissions = list(user.user_permissions.all())
    
    sub_groups = list(sub_obj.groups.all())
    sub_permissions = list(sub_obj.permissions.all())
    
    # Add user to subscription groups
    for group in sub_groups:
        if group not in current_groups:
            user.groups.add(group)
            logger.info(f"User {user.username} added to group {group.name}")
    
    # Remove user from groups not in subscription
    for group in current_groups:
        if group.name.lower() == "default":
            continue
        if group not in sub_groups:
            user.groups.remove(group)
            logger.info(f"User {user.username} removed from group {group.name}")
            
    # Add user permissions from subscription
    for perm in sub_permissions:
        if perm not in current_permissions:
            user.user_permissions.add(perm)
            logger.info(f"Permission {perm.codename} added to user {user.username}")
            
    # Remove user permissions not in subscription
    for perm in current_permissions:
        if perm not in sub_permissions:
            user.user_permissions.remove(perm)
            logger.info(f"Permission {perm.codename} removed from user {user.username}")

post_save.connect(user_sub_post_save, sender=UserSubscription)

def setup_subscription_groups_and_permissions(sender, *args, **kwargs):
    """
    A post-migrate signal handler that creates the default subscription groups
    and permissions.
    """
    if not ALLOW_CUSTOM_GROUPS:
        return
    
    free_trial_group, created = Group.objects.get_or_create(name='free-trial')
    if created:
        logger.info("Created 'free-trial' group.")
    
    default_group, created = Group.objects.get_or_create(name='default')
    if created:
        logger.info("Created 'default' group.")
        
    member_group, created = Group.objects.get_or_create(name='member')
    if created:
        logger.info("Created 'member' group.")

post_save.connect(setup_subscription_groups_and_permissions, sender=Subscription)
