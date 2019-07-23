from django.test import TestCase

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_user_valid(self):
        """Test for creating a valid user successfully"""
        payload = {
            'email': 'test@recipeapi.com',
            'password': 'somethingrandom'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_exists(self):
        """Test for creating a user that already exists"""
        payload = {
            'email': 'test@recipeapi.com',
            'password': 'somethingrandom'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test for creating a user with short password"""
        payload = {
            'email': 'test@recipeapi.com',
            'password': 'sr'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_token_valid_user(self):
        """Test that token is created if user is valid"""
        payload = {
            'email': 'test@recipeapi.com',
            'password': 'somethingrandom'
        }
        create_user(**payload)

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_token_invalid_user(self):
        """Test that token is not created if user is invalid"""
        create_user(
            email='test@recipeapi.com',
            password='somethingwrongpassword'
        )
        payload = {
            'email': 'test@recipeapi.com',
            'password': 'somethingrandom'
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_no_user(self):
        """Test that token is not created if user does not exist"""
        payload = {
            'email': 'test@recipeapi.com',
            'password': 'somethingrandom'
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_invalid_fields(self):
        """Test that token is not created if payload fields are invalid"""
        create_user(email='test@recipeapi.com', password='somethingrandom')
        payload = {
            'email': 'test@recipeapi.com',
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthenticated(self):
        """Test that authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self) -> None:
        self.user = create_user(
            email='test@recipeapi.com',
            password='somethingrandom'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_authenticated(self):
        """Test that authenticated user can get profile"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': 'test@recipeapi.com'
        })

    def test_post_me_not_allowed(self):
        """Test that post method is not allowed on me url"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test that user can update profile"""
        payload = {'password': 'somethingnewpassword'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(payload['password']))
