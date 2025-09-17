from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

class DashboardViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_dashboard_view_authenticated_user(self):
        """
        Tests that an authenticated user can access the dashboard.
        """
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/main.html')

    def test_dashboard_view_unauthenticated_user(self):
        """
        Tests that an unauthenticated user is redirected to the landing page.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing/main.html')

    def test_dashboard_content(self):
        """
        Tests that the dashboard contains the expected content.
        """
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertContains(response, "Use your AI Now")
