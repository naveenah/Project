import logging
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st, settings
from .views import VALID_CODE

logger = logging.getLogger(__name__)
logger.info("genapp tests loaded")

class GenappViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        Group.objects.get_or_create(name='free-trial')
        self.user = User.objects.create_user(username='testuser', password='password')
        self.staff_user = User.objects.create_user(username='staffuser', password='password', is_staff=True)
        self.superuser = User.objects.create_superuser(username='superuser', password='password')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing/main.html')

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_pw_protected_view_authenticated(self):
        session = self.client.session
        session['protected_page_allowed'] = 1
        session.save()
        response = self.client.get(reverse('pw_protected'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'genapp/protected.html')

    def test_pw_protected_view_unauthenticated(self):
        response = self.client.get(reverse('pw_protected'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'protected/entry.html')

    def test_user_only_view_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('user_only'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'genapp/user_only.html')

    def test_user_only_view_unauthenticated(self):
        response = self.client.get(reverse('user_only'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('user_only')}")

    def test_staff_only_view_staff(self):
        self.client.login(username='staffuser', password='password')
        response = self.client.get(reverse('staff_only'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'genapp/staff_only.html')

    def test_staff_only_view_non_staff(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('staff_only'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('staff_only')}", fetch_redirect_response=False)

    def test_staff_only_view_unauthenticated(self):
        response = self.client.get(reverse('staff_only'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('staff_only')}")

class GenappHypothesisViewsTest(HypothesisTestCase):
    def setUp(self):
        self.client = Client()

    @settings(deadline=None)
    @given(code=st.text())
    def test_pw_protected_view_hypothesis(self, code):
        """
        Tests the password-protected view with various inputs.
        """
        response = self.client.post(reverse('pw_protected'), {'code': code})
        
        if code == VALID_CODE:
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'genapp/protected.html')
            self.assertEqual(self.client.session.get('protected_page_allowed'), 1)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'protected/entry.html')
            # Ensure the session is not set for invalid codes
            if 'protected_page_allowed' in self.client.session:
                 self.assertNotEqual(self.client.session.get('protected_page_allowed'), 1)
