import logging
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from subscriptions.models import Subscription, SubscriptionPrice, UserSubscription
from customers.models import Customer
import helpers.billing
from unittest.mock import patch
from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st, settings

logger = logging.getLogger(__name__)
logger.info("checkouts tests loaded")

class CheckoutsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        Group.objects.get_or_create(name='free-trial')
        self.user = User.objects.create_user(username='testuser', password='password')
        self.customer = Customer.objects.create(user=self.user, stripe_id='cus_test')
        self.subscription = Subscription.objects.create(name='Test Subscription', stripe_id='sub_test')
        self.price = SubscriptionPrice.objects.create(subscription=self.subscription, stripe_id='price_test', price=1000)

    def test_product_price_redirect_view(self):
        response = self.client.get(reverse('sub-price-checkout', kwargs={'price_id': self.price.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('stripe-checkout-start'), fetch_redirect_response=False)
        self.assertEqual(self.client.session['checkout_subscription_price_id'], self.price.id)

    @patch('helpers.billing.start_checkout_session')
    def test_checkout_redirect_view(self, mock_start_checkout_session):
        mock_start_checkout_session.return_value = 'http://test.url'
        self.client.login(username='testuser', password='password')
        session = self.client.session
        session['checkout_subscription_price_id'] = self.price.id
        session.save()
        response = self.client.get(reverse('stripe-checkout-start'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, 'http://test.url', fetch_redirect_response=False)

    @patch('stripe.Subscription.retrieve')
    @patch('stripe.checkout.Session.retrieve')
    def test_checkout_finalize_view(self, mock_stripe_session_retrieve, mock_stripe_sub_retrieve):
        mock_stripe_session_retrieve.return_value.client_reference_id = self.user.id
        mock_stripe_session_retrieve.return_value.customer = 'some_customer_id'
        mock_stripe_session_retrieve.return_value.subscription = 'some_sub_id'

        mock_stripe_sub_retrieve.return_value.plan.id = self.price.stripe_id

        session = self.client.session
        session['checkout_session_id'] = 'some_session_id'
        session.save()

        url = f"{reverse('stripe-checkout-end')}?session_id=some_session_id"
        response = self.client.get(url)

        user_sub = UserSubscription.objects.get(user=self.user)
        self.assertRedirects(response, user_sub.get_absolute_url())

class CheckoutsHypothesisViewsTest(HypothesisTestCase):
    def setUp(self):
        self.client = Client()
        Group.objects.get_or_create(name='free-trial')
        self.user = User.objects.create_user(username='testuser', password='password')
        self.customer = Customer.objects.create(user=self.user, stripe_id='cus_test')
        self.subscription = Subscription.objects.create(name='Test Subscription', stripe_id='sub_test')
        self.price = SubscriptionPrice.objects.create(subscription=self.subscription, stripe_id='price_test', price=1000)

    @given(price_id=st.integers(min_value=0))
    @settings(deadline=None)
    def test_product_price_redirect_view_hypothesis(self, price_id):
        """
        Tests the product_price_redirect_view with a range of integers for price_id.
        """
        self.client.login(username='testuser', password='password')
        # Ensure the generated id is not the valid one, to test the 404 case,
        # but also allow the valid case to be tested.
        if price_id == self.price.id:
            url = reverse('sub-price-checkout', kwargs={'price_id': self.price.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('stripe-checkout-start'), fetch_redirect_response=False)
            self.assertEqual(self.client.session['checkout_subscription_price_id'], self.price.id)
        else:
            url = reverse('sub-price-checkout', kwargs={'price_id': price_id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('pricing'))

