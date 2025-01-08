import helpers.billing
from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.db.models.signals import post_save

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
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(Permission, 
    limit_choices_to={
        "content_type__app_label":"subscriptions",
        "codename__in":[x[0]for x in SUBSCRIPTION_PERMISSION]
        }
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        permissions= SUBSCRIPTION_PERMISSION

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

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription =  models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance 
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.value_list('groups_id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups)
    else:
        subs_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            sub_qs = sub_qs.exclude(id=subscription_obj.id)
        sub_groups = subs_qs.value_list('groups__id', flat=True)
        sub_groups_set = set(sub_groups)
        current_groups = user.groups.all().value_list('id', flat=True)
        group_ids_set = set(group_ids)
        current_groups_set = set(current_groups) - sub_groups_set
        final_group_ids = list(group_ids_set | current_groups_set)
        user.groups.set(final_group_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)
