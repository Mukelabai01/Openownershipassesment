from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass')

    def test_login_sets_refresh_cookie_and_returns_access(self):
        url = reverse('token_obtain')
        resp = self.client.post(url, data={'username': 'alice', 'password': 'pass'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        # Cookie set
        self.assertIn('refresh', resp.cookies)

    def test_refresh_returns_new_access(self):
        # login first
        url = reverse('token_obtain')
        resp = self.client.post(url, data={'username': 'alice', 'password': 'pass'}, format='json')
        self.assertIn('refresh', resp.cookies)
        # Extract refresh token from cookies for manual passing (test environment)
        refresh_token = resp.cookies.get('refresh').value
        # call refresh endpoint with refresh token in body
        url2 = reverse('token_refresh')
        resp2 = self.client.post(url2, data={'refresh': refresh_token}, format='json')
        if resp2.status_code != 200:
            print(f"Error response: {resp2.data}")
        self.assertEqual(resp2.status_code, 200)
        self.assertIn('access', resp2.data)

    def test_me_requires_access(self):
        me_url = reverse('me')
        # no auth
        resp = self.client.get(me_url)
        self.assertEqual(resp.status_code, 401)
        # obtain access via login
        login_url = reverse('token_obtain')
        resp = self.client.post(login_url, data={'username': 'alice', 'password': 'pass'}, format='json')
        access = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp2 = self.client.get(me_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['username'], 'alice')
