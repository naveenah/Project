import logging
import helpers.billing 
from django.conf import settings
from django.db import models
from allauth.account.signals import(
    user_signed_up as allauth_user_signed_up,
    email_confirmed as allauth_email_confirmed
)

User = settings.AUTH_USER_MODEL
logger = logging.getLogger(__name__)

# Create your models here.
class Customer(models.Model):
    """
    Represents a customer in the system, linking a user to a Stripe customer ID.

    Attributes:
        user (User): A one-to-one relationship with the User model.
        stripe_id (str): The customer's ID in Stripe.
        init_email (str): The initial email address provided during signup.
        init_email_confirmed (bool): Whether the initial email has been confirmed.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(blank=True, null=True)
    init_email_confirmed = models.BooleanField(default = False)

    def __str__(self):
        return f"{self.user.username}"
    
    def save(self, *args, **kwargs):
        """
        Saves the Customer instance.

        If the customer does not have a Stripe ID and their initial email is confirmed,
        a new Stripe customer is created and the `stripe_id` is set.
        """
        if not self.stripe_id:
            if self.init_email_confirmed and self.init_email:
                email = self.init_email
                if email != "" or email is not None:
                    try:
                        logger.info(f"Creating Stripe customer for user {self.user.username} with email {email}")
                        stripe_id = helpers.billing.create_customer(email=email,
                                                                    metadata={"user_id":self.user.id,
                                                                              "username":self.user.username},
                                                                    raw=False)
                        self.stripe_id = stripe_id
                        logger.info(f"Stripe customer created for user {self.user.username} with stripe_id {stripe_id}")
                    except Exception as e:
                        logger.error(f"Error creating Stripe customer for user {self.user.username}: {e}", exc_info=True)
        super().save(*args, **kwargs)

def allauth_user_signed_up_handler(request,user, *args, **kwargs):
    """
    Handles the `user_signed_up` signal from `allauth`.

    Creates a new `Customer` instance for the newly signed-up user.

    Args:
        request: The HTTP request.
        user (User): The user who signed up.
    """
    email = user.email
    logger.info(f"New user signed up: {user.username} with email {email}")
    try:
        Customer.objects.create(
            user = user,
            init_email = email,
            init_email_confirmed = False,
        )
        logger.info(f"Customer object created for user {user.username}")
    except Exception as e:
        logger.error(f"Error creating customer for user {user.username}: {e}", exc_info=True)

allauth_user_signed_up.connect(allauth_user_signed_up_handler)

def allauth_email_confirmed_handler(request,email_address, *args, **kwargs):
    """
    Handles the `email_confirmed` signal from `allauth`.

    When an email is confirmed, this function finds the corresponding `Customer`
    and marks their email as confirmed, which may trigger the creation of a
    Stripe customer ID.

    Args:
        request: The HTTP request.
        email_address (EmailAddress): The email address that was confirmed.
    """
    logger.info(f"Email confirmed: {email_address.email}")
    qs = Customer.objects.filter(
        init_email=email_address.email,
        init_email_confirmed = False,
    )
    # Does not send the save method or create the stripe customer
    # qs.update(init_email_confirmed=True)
    for obj in qs:
        try:
            obj.init_email_confirmed = True;
            obj.save()
            logger.info(f"Customer email confirmed for user {obj.user.username}")
        except Exception as e:
            logger.error(f"Error confirming email for customer with email {email_address.email}: {e}", exc_info=True)

allauth_email_confirmed.connect(allauth_email_confirmed_handler)