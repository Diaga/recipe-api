import tempfile
import os

from PIL import Image

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Ingredient, Recipe
from ..serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return url for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_user(email='test@recipeapi.com', password='somethingrandom'):
    """Creates a sample user"""
    return get_user_model().objects.create_user(
        email, password
    )


def sample_tag(user, name='Main Course'):
    """Creates a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Creates a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 2
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe api access"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe api access"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()

        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving recipes"""
        sample_recipe(self.user)
        sample_recipe(self.user, title="Sample recipe 2")

        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipes_valid(self):
        """Test retrieving recipes for authenticated user only"""
        user_test = sample_user(email='other@recipeapi.com')

        sample_recipe(self.user)
        sample_recipe(user_test, title='Recipe test')

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(len(res.data), 1)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)

        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 10,
            'price': 5.00
        }
        res = self.client.post(RECIPES_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_tags_recipe(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user)
        tag2 = sample_tag(user=self.user, name='Vegan')

        payload = {
            'title': 'Avocado Lime Cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 20,
            'price': 10.00
        }
        res = self.client.post(RECIPES_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_ingredients_recipe(self):
        """Test creating a recipe with ingredients"""
        ingredient_1 = sample_ingredient(user=self.user)
        ingredient_2 = sample_ingredient(user=self.user, name='Ginger')

        payload = {
            'title': 'Red Curry',
            'time_minutes': 10,
            'price': 25.00,
            'ingredients': [ingredient_1.id, ingredient_2.id]
        }
        res = self.client.post(RECIPES_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_1, ingredients)
        self.assertIn(ingredient_2, ingredients)

    def test_update_partial_recipe(self):
        """Test updating recipe partially"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        new_tag = sample_tag(user=self.user, name='Dessert')

        payload = {'title': 'Chicken Tikka', 'tags': [new_tag.id]}

        url = detail_url(recipe.id)

        self.client.patch(url, payload)

        recipe.refresh_from_db()
        tags = recipe.tags.all()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_update_full_recipe(self):
        """Test updating recipe fully"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Spaghetti Carbonara',
            'time_minutes': 25,
            'price': 3.00
        }
        url = detail_url(recipe.id)

        self.client.put(url, payload)

        recipe.refresh_from_db()
        tags = recipe.tags.all()

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

        self.assertEqual(tags.count(), 0)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe_tag_1 = sample_recipe(user=self.user)
        recipe_tag_2 = sample_recipe(user=self.user, title='Samosa')
        recipe_no_tag = sample_recipe(user=self.user, title='Rice')

        tag_1 = sample_tag(user=self.user)
        tag_2 = sample_tag(user=self.user, name='Fried')

        recipe_tag_1.tags.add(tag_1)
        recipe_tag_2.tags.add(tag_2)

        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag_1.id},{tag_2.id}'}
        )

        serializer_1 = RecipeSerializer(recipe_tag_1)
        serializer_2 = RecipeSerializer(recipe_tag_2)
        serializer_no = RecipeSerializer(recipe_no_tag)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_no.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test filtering recipes by ingredients"""
        recipe_ing_1 = sample_recipe(user=self.user)
        recipe_ing_2 = sample_recipe(user=self.user, title='Chips')
        recipe_ing_no = sample_recipe(user=self.user, title='Pizza')

        ing_1 = sample_ingredient(user=self.user)
        ing_2 = sample_ingredient(user=self.user, name='Potatoes')

        recipe_ing_1.ingredients.add(ing_1)
        recipe_ing_2.ingredients.add(ing_2)

        res = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ing_1.id},{ing_2.id}'}
        )

        serializer_1 = RecipeSerializer(recipe_ing_1)
        serializer_2 = RecipeSerializer(recipe_ing_2)
        serializer_no = RecipeSerializer(recipe_ing_no)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_no.data, res.data)


class RecipeImageUploadTests(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()

        self.client.force_authenticate(user=self.user)

        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_valid(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_invalid(self):
        """Test uploading an invalid image to recipe"""
        url = image_upload_url(self.recipe.id)

        res = self.client.post(url, {'image': 'not_image'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
