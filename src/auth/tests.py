from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from hypothesis.extra.django import TestCase as HypothesisTestCase
from hypothesis import given, strategies as st, settings

# Strategy for text that avoids null characters and surrogates, as they can cause issues with databases and other systems.
safe_text = st.text(alphabet=st.characters(min_codepoint=1, max_codepoint=0xD7FF))

class AuthViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.get_or_create(name='free-trial')

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')

    def test_login_view_get(self):
        """
        Tests that the login view renders correctly.
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')

    def test_login_view_post_success(self):
        """
        Tests that a user can log in successfully.
        """
        User.objects.create_user(username='testuser', password='password')
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'password'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_fail(self):
        """
        Tests that a user cannot log in with incorrect credentials.
        """
        User.objects.create_user(username='testuser', password='password')
        response = self.client.post(self.login_url, {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response, "Please enter a correct username and password. Note that both fields may be case-sensitive.")

class AuthHypothesisTests(HypothesisTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.get_or_create(name='free-trial')
        
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.password = "password"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    @settings(deadline=None)
    @given(
        username=safe_text,
        password=safe_text
    )
    def test_login_view_handles_various_inputs(self, username, password):
        """
        Tests that the login view handles a wide variety of username and password inputs without crashing.
        """
        response = self.client.post(reverse('login'), {'username': username, 'password': password})
        self.assertIn(response.status_code, [200, 302, 400])

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')

    def test_login_view_post_success(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'password'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_fail(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/register.html')

class AuthHypothesisTests(HypothesisTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.get_or_create(name='free-trial')
        
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.password = "password"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    @settings(deadline=None)
    @given(
        username=safe_text,
        password=safe_text
    )
    def test_login_view_handles_various_inputs(self, username, password):
        """
        Tests that the login view handles a wide variety of username and password inputs without crashing.
        """
        response = self.client.post(reverse('login'), {'username': username, 'password': password})

        # If the credentials happen to be correct, we expect a redirect.
        if username == self.username and password == self.password:
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('home'))
        # Otherwise, we expect the login page to be rendered again.
        else:
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'auth/login.html')

