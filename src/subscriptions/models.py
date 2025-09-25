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

User = settings.AUTH_USER_MODEL
ALLOW_CUSTOM_GROUPS=True

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
        return [x.strip() for x in self.features.split("\n")]    

    def save(self, *args, **kwargs):
        """
        Saves the subscription and creates a corresponding Stripe Product if one
        does not already exist.
        """
        if not self.stripe_id:
            stripe_id = helpers.billing.create_product(
                name=self.name,
                metadata={
                        "subscription_plan_id":self.id,
                        },
                        raw=False
                    )
            self.stripe_id = stripe_id
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

    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL,null=True)
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

    class Meta:
        ordering = ['subscription__order','order', 'featured','-updated']

    def get_checkout_url(self):
        """
        Returns the URL for the checkout page for this price.
        """
        return reverse("sub-price-checkout", kwargs={"price_id": self.id})

    @property
    def display_features_list(self):
        """
        Returns the features of the associated subscription as a list of strings.
        """
        if not self.subscription:
            return []
        return self.subscription.get_features_as_list()    

    @property
    def display_sub_name(self):
        """
        Returns the name of the associated subscription.
        """
        if not self.subscription:
            return ""
        return self.subscription.name

    @property
    def display_price(self):
        """
        Returns the price in a human-readable format.
        """
        return helpers.numbers.humanize_price(self.price)

    def save(self, *args, **kwargs):
        """
        Saves the price and creates a corresponding Stripe Price if one does not
        already exist.
        """
        if not self.stripe_id and self.subscription and self.subscription.stripe_id:
            stripe_id = helpers.billing.create_price(
                product=self.subscription.stripe_id,
                unit_amount=int(self.price * 100),
                currency="usd",
                interval=self.interval,
                metadata={
                        "subscription_price_id":self.id,
                        },
                        raw=False
                    )
            self.stripe_id = stripe_id
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

    @property
    def is_active(self):
        """
        Returns True if the subscription is active, False otherwise.
        """
        return self.status == "active"

    def get_absolute_url(self):
        """
        Returns the URL for the user's subscription detail page.
        """
        return reverse("user_subscription")

    def __str__(self):
        return f"{self.user.username}"

    def save(self, *args, **kwargs):
        """
        Saves the user subscription.
        """
        if self.is_active:
            if self.subscription:
                for grp in self.subscription.groups.all():
                    grp.user_set.add(self.user)
                for perm_obj in self.subscription.permissions.all():
                    self.user.user_permissions.add(perm_obj)
            else:
                # remove all perms
                pass
        super().save(*args, **kwargs)

def post_save_user_subscription_receiver(sender, instance, created, *args, **kwargs):
    """
    A signal receiver that is called after a UserSubscription is saved.
    """
    if created:
        pass

post_save.connect(post_save_user_subscription_receiver, sender=UserSubscription)

def user_subscription_post_save_receiver(sender, instance, created, *args, **kwargs):
    """
    A signal receiver that is called after a User is saved.
    """
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=instance)
    if ALLOW_CUSTOM_GROUPS:
        free_trial_group = Group.objects.get(name='free-trial')
        user_sub_obj.user.groups.add(free_trial_group)

post_save.connect(user_subscription_post_save_receiver, sender=User)
