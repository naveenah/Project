import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import UserSubscription, SubscriptionPrice, Subscription
from django.contrib.auth.models import Group

User = get_user_model()

class SubscriptionViewsTest(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name='free-trial')
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.subscription = Subscription.objects.create(name='Pro')
        self.price_month = SubscriptionPrice.objects.create(
            subscription=self.subscription,
            price=1000,
            interval=SubscriptionPrice.IntervalChoices.MONTHLY,
            featured=True
        )
        self.price_year = SubscriptionPrice.objects.create(
            subscription=self.subscription,
            price=10000,
            interval=SubscriptionPrice.IntervalChoices.YEARLY,
            featured=True
        )

    def test_user_subscription_view_get(self):
        """
        Tests that the user subscription view renders correctly.
        """
        response = self.client.get(reverse('user_subscription'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/user_detail_view.html')

    @patch('subscriptions.utils.refresh_active_users_subscriptions')
    def test_user_subscription_view_post(self, mock_refresh):
        """
        Tests that the user subscription view refreshes the subscription.
        """
        mock_refresh.return_value = True
        response = self.client.post(reverse('user_subscription'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_subscription'))

    def test_user_subscription_cancel_view_get(self):
        """
        Tests that the cancel subscription view renders correctly.
        """
        response = self.client.get(reverse('user_subscription_cancel'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/user_cancel_view.html')

    @patch('helpers.billing.cancel_subscription')
    def test_user_subscription_cancel_view_post(self, mock_cancel):
        """
        Tests that the cancel subscription view cancels the subscription.
        """
        user_sub = UserSubscription.objects.get(user=self.user)
        user_sub.stripe_id = 'sub_123'
        user_sub.save()
        mock_cancel.return_value = {
            'status': 'canceled',
            'current_period_start': datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
            'current_period_end': datetime.datetime(2023, 2, 1, tzinfo=datetime.timezone.utc),
            'cancel_at_period_end': True,
        }
        response = self.client.post(reverse('user_subscription_cancel'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user_subscription'))
        user_sub.refresh_from_db()
        self.assertTrue(user_sub.cancel_at_period_end)

    def test_subscription_price_view_monthly(self):
        """
        Tests that the pricing page shows monthly prices.
        """
        response = self.client.get(reverse('pricing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/pricing.html')
        self.assertContains(response, 'Pro')

    def test_subscription_price_view_yearly(self):
        """
        Tests that the pricing page shows yearly prices.
        """
        response = self.client.get(reverse('pricing_interval', kwargs={'interval': 'year'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'subscriptions/pricing.html')
        self.assertContains(response, 'Pro')
