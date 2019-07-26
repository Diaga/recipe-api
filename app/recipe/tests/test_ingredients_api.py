from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from ..serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def sample_user(email='test@recipeapi.com', password='somethingrandom'):
    """Creates a sample user for tests"""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsApiTests(TestCase):
    """Test the public ingredients api"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for access"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the private ingredients api"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        ingredients = Ingredient.objects.all().order_by('-name')

        serializer = IngredientSerializer(ingredients, many=True)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_valid_user(self):
        """Test that only ingredients for authenticated users are returned"""
        user_test = sample_user(
            email='test2@recipeapi.com',
            password='somethingrandom2'
        )

        Ingredient.objects.create(user=user_test, name='ingredient test')
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='ingredient auth'
        )

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_valid(self):
        """Test that ingredient is created successfully"""
        payload = {'name': 'cabbage'}

        res = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            name=payload['name']
        ).exists()

        self.assertTrue(exists)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload['name'], res.data['name'])

    def test_craete_ingredient_invalid(self):
        """Test that ingredient creation fails with invalid payload"""
        payload = {'name': ''}

        res = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(exists)

    def test_retrieving_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients assigned to recipes"""
        ing_1 = Ingredient.objects.create(
            user=self.user,
            name='Salt'
        )
        ing_2 = Ingredient.objects.create(
            user=self.user,
            name='Potatoes'
        )

        recipe = Recipe.objects.create(
            user=self.user,
            title='Fries',
            time_minutes=5,
            price=10.00
        )

        recipe.ingredients.add(ing_2)

        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only': 1}
        )

        serializer_1 = IngredientSerializer(ing_1)
        serializer_2 = IngredientSerializer(ing_2)

        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
