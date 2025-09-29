from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse
from unittest.mock import patch
from visits.models import PageVisits

class LandingDashboardPageViewTest(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name='free-trial')
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_landing_page_authenticated_user(self):
        """
        Tests that an authenticated user is redirected to the dashboard.
        """
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/main.html')

    @patch('helpers.numbers.shorten_number')
    def test_landing_page_unauthenticated_user(self, mock_shorten_number):
        """
        Tests that an unauthenticated user sees the landing page with view counts.
        """
        mock_shorten_number.side_effect = ['1K', '1K']
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing/main.html')
        self.assertEqual(PageVisits.objects.count(), 1)
        self.assertContains(response, '1K')
