import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import UserSubscription, SubscriptionPrice, Subscription
from django.contrib.auth.models import Group

from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st, settings

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

safe_text = st.text(alphabet=st.characters(blacklist_characters='\\x00'))

class SubscriptionHypothesisTest(HypothesisTestCase):
    @settings(deadline=None)
    @given(
        name=safe_text.map(lambda s: s[:120]).filter(lambda s: len(s) > 0),
        subtitle=st.one_of(st.none(), safe_text),
        active=st.booleans(),
        order=st.integers(min_value=-2147483648, max_value=2147483647),
        featured=st.booleans(),
        features=st.one_of(st.none(), safe_text),
    )
    @patch('helpers.billing.create_product')
    def test_subscription_model_save_hypothesis(
        self, mock_create_product, name, subtitle, active, order, featured, features
    ):
        """
        Tests the Subscription model's save method with various inputs.
        """
        mock_create_product.return_value = "prod_test_hypothesis"
        
        sub = Subscription(
            name=name,
            subtitle=subtitle,
            active=active,
            order=order,
            featured=featured,
            features=features,
        )
        sub.save()

        self.assertEqual(sub.name, name)
        self.assertEqual(sub.subtitle, subtitle)
        self.assertEqual(sub.active, active)
        self.assertEqual(sub.order, order)
        self.assertEqual(sub.featured, featured)
        self.assertEqual(sub.features, features)
        
        # Stripe product should be created only if stripe_id is not set
        mock_create_product.assert_called_once()
        self.assertEqual(sub.stripe_id, "prod_test_hypothesis")

        # Test get_features_as_list
        if features:
            self.assertEqual(sub.get_features_as_list(), [x.strip() for x in features.split("\\n")])
        else:
            self.assertEqual(sub.get_features_as_list(), [])

class SubscriptionPriceHypothesisTest(HypothesisTestCase):
    def setUp(self):
        self.subscription = Subscription.objects.create(name='Test Subscription')

    @settings(deadline=None)
    @given(
        price=st.decimals(min_value=0, max_value=100000, places=2),
        interval=st.sampled_from([x[0] for x in SubscriptionPrice.IntervalChoices.choices]),
        order=st.integers(min_value=-2147483648, max_value=2147483647),
        featured=st.booleans(),
    )
    @patch('helpers.billing.create_price')
    def test_subscription_price_model_save_hypothesis(
        self, mock_create_price, price, interval, order, featured
    ):
        """
        Tests the SubscriptionPrice model's save method with various inputs.
        """
        mock_create_price.return_value = "price_test_hypothesis"
        
        sub_price = SubscriptionPrice(
            subscription=self.subscription,
            price=price,
            interval=interval,
            order=order,
            featured=featured,
        )
        sub_price.save()

        self.assertEqual(sub_price.subscription, self.subscription)
        self.assertEqual(sub_price.price, price)
        self.assertEqual(sub_price.interval, interval)
        self.assertEqual(sub_price.order, order)
        self.assertEqual(sub_price.featured, featured)
        
        # Stripe price should be created only if stripe_id is not set
        mock_create_price.assert_called_once()
        self.assertEqual(sub_price.stripe_id, "price_test_hypothesis")
