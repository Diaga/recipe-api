from django.test import TestCase

from django.contrib.auth import get_user_model


class UserModelTests(TestCase):

    def test_create_user(self):
        """Tests whether a user is created successfully"""
        email = "test@recipeapi.com"
        password = "password_for_test_create_user"

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_user_email_normalized(self):
        """Tests if a user's email is normalized"""
        email = "tesT@recipeAPI.com"
        password = "somethingrandom"

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        normalized_email = "@".join([email.split("@")[0],
                                     email.split("@")[1].lower()])
        self.assertEqual(user.email, normalized_email)

    def test_user_no_email_raises_error(self):
        """Tests if creating a user with no email raises a value error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                password="somethingrandom"
            )

    def test_create_superuser(self):
        """Tests creating and saving a superuser"""
        user = get_user_model().objects.create_superuser(
            email="superuser@recipeapi.com",
            password="somethingrandom"
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
