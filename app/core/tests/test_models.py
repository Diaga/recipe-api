from django.test import TestCase

from django.contrib.auth import get_user_model

from .. import models


def sample_user(email='test@recipeapi.com', password='somethingrandom'):
    """Creates a sample user for tests"""
    return get_user_model().objects.create_user(email=email, password=password)


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


class TagModelTests(TestCase):

    def test_tag_str(self):
        """Test that tag object returns a string representation"""
        tag = models.Tag.objects.create(
            name='test tag',
            user=sample_user()
        )

        self.assertEqual(str(tag), tag.name)


class IngredientModelTests(TestCase):

    def test_ingredient_str(self):
        """Test that ingredient object returns a string representation"""
        ingredient = models.Ingredient.objects.create(
            name='test ingredient',
            user=sample_user()
        )

        self.assertEqual(str(ingredient), ingredient.name)


class RecipeModelTests(TestCase):

    def test_recipe_str(self):
        """Test that recipe object returns a string representation"""
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='Pizza',
            time_minutes=5,
            price=5.00
        )

        self.assertEqual(str(recipe), recipe.title)
