from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from subscriptions.models import Subscription, SubscriptionPrice, UserSubscription
from customers.models import Customer
import helpers.billing
from unittest.mock import patch

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

    @patch('helpers.billing.get_checkout_customer_plan')
    def test_checkout_finalize_view(self, mock_get_checkout_customer_plan):
        mock_get_checkout_customer_plan.return_value = {
            'plan_id': self.price.stripe_id,
            'customer_id': self.customer.stripe_id,
            'sub_stripe_id': 'sub_stripe_123',
        }
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('stripe-checkout-end'), {'session_id': 'test_session'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_subscription'))
        self.assertTrue(UserSubscription.objects.filter(user=self.user).exists())

