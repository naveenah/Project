import helpers.billing
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.db.models.signals import post_save
from django.urls import reverse

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
    Subscription Product Model = Stripe Product
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
        if not self.features:
            return []
        return [x.strip() for x in self.features.split("\n")]    

    def save(self, *args, **kwargs):
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
    Subscription Price Model = Stripe Price
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
        return reverse("sub-price-checkout", kwargs={"price_id": self.id})

    @property
    def display_features_list(self):
        if not self.subscription:
            return []
        return self.subscription.get_features_as_list()    

    @property
    def display_sub_name(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.name    
    
    @property
    def display_sub_subtitle(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle    
    
    @property
    def stripe_price(self):
        """
        Remove decimal places
        """
        return int(self.price * 100)
    
    @property
    def stripe_currency(self):
        return "usd"

    @property
    def product_stripe_id(self):
        if not self.subscription:
            return None
        return self.subscription.stripe_id
    
    def save(self, *args, **kwargs):
        if (not self.stripe_id and 
            self.product_stripe_id is not None): 
            import stripe
            stripe.api_key = "sk_test_51QWbqXEiMLm0Ho7OfbXfS7CUkuAGMbb2s6qM1kVl2D62g7aTdkBRNR49CvlhbJAIuJRPY26wPGjlEMxgJy5AH4hi00YFRrQ1X5"
            stripe_id = helpers.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                product=self.product_stripe_id,
                metadata={
                        "subscription_plan_price_id":self.id,
                        },
                raw = False        
            )
            self.stripe_id = stripe_id 

        super().save(*args,**kwargs)
        if self.featured and self.subscription:
            qs = SubscriptionPrice.objects.filter(
                subscription = self.subscription,
                interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)

class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', 'ACTIVE'
        TRAILING = 'trailing', 'TRAILING'
        INCOMPLETE = 'incomplete','INCOMPLETE'
        INCOMPLETE_EXPIRED = 'incomplete_expired', 'INCOMPLETE_EXPIRED'
        PAST_DUE = 'past_due','PAST_DUE'
        CANCELLED = 'cancelled','CANCELLED'
        UNPAID = 'unpaid','UNPAID'
        PAUSED = 'paused','PAUSED'

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription =  models.ForeignKey(
        Subscription, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
        )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(
        auto_now=False, 
        auto_now_add=False, 
        blank=True, 
        null=True
        )
    current_period_start = models.DateTimeField(
        auto_now=False, 
        auto_now_add=False, 
        blank=True, 
        null=True
        )
    current_period_end = models.DateTimeField(
        auto_now=False, 
        auto_now_add=False, 
        blank=True, 
        null=True
        )     
    status = models.CharField(
        max_length=20, 
        choices=SubscriptionStatus.choices, 
        null=True, 
        blank=True)
    calncel_at_period_end = models.BooleanField(default=False)
    
    def get_absolute_url(self):
        return reverse("user_subscription")
    
    def get_cancel_url(self):
        return reverse("user_subscription_cancel")
    
    @property
    def plan_name(self):
        if not self.subscription:
            return None
        return self.subscription.name
    
    @property
    def is_active_status(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRAILING]
    
    def serialize(self):
        return {
            "plan_name": self.plan_name,
            "status": self.status,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
        }
    
    @property
    def billing_cycle_anchor(self):
        """
        https://docs.stripe.com/payments/checkout/billing-cycle
        Optional delay to start new subscription in Stripe checkout
        """
        if not self.current_period_end:
            return None
        return int(self.current_period_end.timestamp())
    
    def save(self, *args, **kwargs):
        if(self.original_period_start is None and self.current_period_start is not None):
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance 
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        sub_groups = subs_qs.values_list('groups__id', flat=True)
        sub_groups_set = set(sub_groups)
        current_groups = user.groups.all().values_list('id', flat=True)
        group_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - sub_groups_set
        final_group_ids = list(group_ids_set | current_groups_set)
        user.groups.set(final_group_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)
