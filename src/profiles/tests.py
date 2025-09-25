from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class ProfileListViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.client.login(username='user1', password='password')

    def test_profile_list_view(self):
        """
        Tests that the profile list view returns a list of active users.
        """
        response = self.client.get(reverse('profiles:profile_list_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/list.html')
        self.assertContains(response, 'user1')
        self.assertContains(response, 'user2')

    def test_profile_list_view_unauthenticated(self):
        """
        Tests that an unauthenticated user is redirected to the login page.
        """
        self.client.logout()
        response = self.client.get(reverse('profiles:profile_list_view'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/profiles/')

class ProfileDetailViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.client.login(username='user1', password='password')

    def test_profile_detail_view_own_profile(self):
        """
        Tests that a user can view their own profile.
        """
        response = self.client.get(reverse('profiles:profile_detail_view', kwargs={'username': 'user1'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/detail.html')
        self.assertTrue(response.context['owner'])
        self.assertContains(response, 'user1')

    def test_profile_detail_view_other_profile(self):
        """
        Tests that a user can view another user's profile.
        """
        response = self.client.get(reverse('profiles:profile_detail_view', kwargs={'username': 'user2'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/detail.html')
        self.assertFalse(response.context['owner'])
        self.assertContains(response, 'user2')

    def test_profile_detail_view_not_found(self):
        """
        Tests that a 404 is returned for a non-existent profile.
        """
        response = self.client.get(reverse('profiles:profile_detail_view', kwargs={'username': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)

    def test_profile_detail_view_unauthenticated(self):
        """
        Tests that an unauthenticated user is redirected to the login page.
        """
        self.client.logout()
        response = self.client.get(reverse('profiles:profile_detail_view', kwargs={'username': 'user1'}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/profiles/user1/')
