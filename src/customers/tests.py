from django.test import TestCase
from django.contrib.auth.models import User
from .models import Customer, allauth_user_signed_up_handler, allauth_email_confirmed_handler
from allauth.account.models import EmailAddress
from unittest.mock import patch

class CustomerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')

    @patch('helpers.billing.create_customer')
    def test_customer_creation_on_user_signup(self, mock_create_customer):
        mock_create_customer.return_value = 'cus_test'
        allauth_user_signed_up_handler(None, self.user)
        customer = Customer.objects.get(user=self.user)
        self.assertIsNotNone(customer)
        self.assertEqual(customer.init_email, self.user.email)
        self.assertFalse(customer.init_email_confirmed)

    @patch('helpers.billing.create_customer')
    def test_stripe_id_creation_on_email_confirmation(self, mock_create_customer):
        mock_create_customer.return_value = 'cus_test'
        customer = Customer.objects.create(user=self.user, init_email=self.user.email)
        email_address = EmailAddress.objects.create(user=self.user, email=self.user.email, primary=True, verified=False)
        allauth_email_confirmed_handler(None, email_address)
        customer.refresh_from_db()
        self.assertTrue(customer.init_email_confirmed)
        self.assertEqual(customer.stripe_id, 'cus_test')

    def test_customer_str(self):
        customer = Customer.objects.create(user=self.user)
        self.assertEqual(str(customer), self.user.username)

    @patch('helpers.billing.create_customer')
    def test_save_no_stripe_id_created_if_email_not_confirmed(self, mock_create_customer):
        customer = Customer.objects.create(user=self.user, init_email=self.user.email, init_email_confirmed=False)
        customer.save()
        self.assertIsNone(customer.stripe_id)
        mock_create_customer.assert_not_called()

    @patch('helpers.billing.create_customer')
    def test_save_no_stripe_id_created_if_email_is_missing(self, mock_create_customer):
        customer = Customer.objects.create(user=self.user, init_email=None, init_email_confirmed=True)
        customer.save()
        self.assertIsNone(customer.stripe_id)
        mock_create_customer.assert_not_called()

