"""
Tests for the helpers application.
"""
import datetime
import unittest
from unittest.mock import MagicMock, patch

from . import billing, date_utils, downloader, numbers


class BillingTests(unittest.TestCase):
    """
    Test cases for the billing helper functions.
    """

    def test_serialize_subscription_data(self):
        """
        Test that subscription data is serialized correctly.
        """
        mock_subscription = MagicMock()
        mock_subscription.status = "active"
        mock_subscription.current_period_start = 1672531200  # 2023-01-01
        mock_subscription.current_period_end = 1675209600  # 2023-02-01
        mock_subscription.cancel_at_period_end = False

        with patch("helpers.date_utils.timestamp_as_datetime") as mock_ts:
            mock_ts.side_effect = [
                datetime.datetime(2023, 1, 1),
                datetime.datetime(2023, 2, 1),
            ]
            data = billing.serialize_subscription_data(mock_subscription)
            self.assertEqual(data["status"], "active")
            self.assertEqual(data["current_period_start"], datetime.datetime(2023, 1, 1))
            self.assertEqual(data["current_period_end"], datetime.datetime(2023, 2, 1))
            self.assertFalse(data["cancel_at_period_end"])

    @patch("stripe.Customer.create")
    def test_create_customer(self, mock_customer_create):
        """
        Test that a Stripe customer is created correctly.
        """
        mock_customer_create.return_value = MagicMock(id="cus_123")
        stripe_id = billing.create_customer(name="Test User", email="test@example.com")
        self.assertEqual(stripe_id, "cus_123")
        mock_customer_create.assert_called_with(
            name="Test User", email="test@example.com", metadata={}
        )

    @patch("stripe.Product.create")
    def test_create_product(self, mock_product_create):
        """
        Test that a Stripe product is created correctly.
        """
        mock_product_create.return_value = MagicMock(id="prod_123")
        stripe_id = billing.create_product(name="Test Product")
        self.assertEqual(stripe_id, "prod_123")
        mock_product_create.assert_called_with(name="Test Product", metadata={})

    @patch("stripe.Price.create")
    def test_create_price(self, mock_price_create):
        """
        Test that a Stripe price is created correctly.
        """
        mock_price_create.return_value = MagicMock(id="price_123")
        stripe_id = billing.create_price(product="prod_123")
        self.assertIsNotNone(stripe_id)
        self.assertEqual(stripe_id, "price_123")
        mock_price_create.assert_called_with(
            currency="usd",
            unit_amount="9999",
            recurring={"interval": "month"},
            product="prod_123",
            metadata={},
        )

    def test_create_price_no_product(self):
        """
        Test that create_price returns None if no product is provided.
        """
        stripe_id = billing.create_price(product=None)
        self.assertIsNone(stripe_id)

    @patch("stripe.checkout.Session.create")
    def test_start_checkout_session(self, mock_session_create):
        """
        Test that a Stripe checkout session is created correctly.
        """
        mock_session_create.return_value = MagicMock(url="http://checkout.url")
        url = billing.start_checkout_session(
            customer_id="cus_123",
            success_url="http://success.url",
            cancel_url="http://cancel.url",
            price_stripe_id="price_123",
            raw=False,
        )
        self.assertEqual(url, "http://checkout.url")
        mock_session_create.assert_called_with(
            customer="cus_123",
            success_url="http://success.url?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://cancel.url",
            line_items=[{"price": "price_123", "quantity": 1}],
            mode="subscription",
        )

    @patch("stripe.checkout.Session.retrieve")
    def test_get_checkout_session(self, mock_session_retrieve):
        """
        Test that a Stripe checkout session is retrieved correctly.
        """
        mock_session_retrieve.return_value = "session_data"
        session = billing.get_checkout_session("sess_123")
        self.assertEqual(session, "session_data")
        mock_session_retrieve.assert_called_with("sess_123")

    @patch("stripe.Subscription.retrieve")
    def test_get_subscription(self, mock_subscription_retrieve):
        """
        Test that a Stripe subscription is retrieved correctly.
        """
        mock_subscription_retrieve.return_value = "sub_data"
        sub = billing.get_subscription("sub_123")
        self.assertEqual(sub, "sub_data")
        mock_subscription_retrieve.assert_called_with("sub_123")

    @patch("stripe.Subscription.cancel")
    def test_cancel_subscription(self, mock_subscription_cancel):
        """
        Test that a Stripe subscription is canceled correctly.
        """
        mock_subscription_cancel.return_value = "canceled_sub_data"
        sub = billing.cancel_subscription("sub_123", reason="Customer service canceled this subscription")
        self.assertEqual(sub, "canceled_sub_data")
        mock_subscription_cancel.assert_called_with(
            "sub_123",
            cancellation_details={
                "comment": "Customer service canceled this subscription",
                "feedback": "other",
            },
        )


class DateUtilsTests(unittest.TestCase):
    """
    Test cases for the date_utils helper functions.
    """

    def test_timestamp_as_datetime(self):
        """
        Test that a timestamp is correctly converted to a datetime object.
        """
        ts = 1672531200  # 2023-01-01 00:00:00 UTC
        dt = date_utils.timestamp_as_datetime(ts)
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)


from pathlib import Path
class DownloaderTests(unittest.TestCase):
    """
    Test cases for the downloader helper functions.
    """

    @patch("requests.get")
    def test_download_to_local(self, mock_requests_get):
        """
        Test that a file is downloaded and saved locally.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"HelloWorld"
        mock_requests_get.return_value = mock_response

        mock_path = MagicMock(spec=Path)
        downloader.download_to_local("http://example.com/file.txt", mock_path)
        mock_path.write_bytes.assert_called_with(b"HelloWorld")


class NumbersTests(unittest.TestCase):
    """
    Test cases for the numbers helper functions.
    """

    def test_shorten_number(self):
        """
        Test that a large number is correctly converted to a shortened format.
        """
        self.assertEqual(numbers.shorten_number(8200000), "8.2M")
        self.assertEqual(numbers.shorten_number(1500000000), "1.5B")
        self.assertEqual(numbers.shorten_number(9000000), "9M")
        self.assertEqual(numbers.shorten_number(1000), "1K")
        self.assertEqual(numbers.shorten_number(100), "100")


from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st

class NumbersHelperHypothesisTest(HypothesisTestCase):
    @given(value=st.integers())
    def test_shorten_number_hypothesis(self, value):
        """
        Tests the shorten_number function with a wide range of integers.
        """
        result = numbers.shorten_number(value)
        self.assertIsInstance(result, str)

        if value < 1000 and value >= 0:
            self.assertEqual(result, str(value))
        
        if value >= 1_000_000_000_000:
            self.assertTrue(result.endswith('T'))
        elif value >= 1_000_000_000:
            self.assertTrue(result.endswith('B'))
        elif value >= 1_000_000:
            self.assertTrue(result.endswith('M'))
        elif value >= 1_000:
            self.assertTrue(result.endswith('K'))

        if value < 0:
            self.assertEqual(result, str(value))

