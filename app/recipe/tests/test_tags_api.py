from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from ..serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def sample_user(email='test@recipeapi.com', password='somethingrandom'):
    """Helper function to create a sample user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test the public tags API"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """"Test that login is required for retreiving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the private tags API"""

    def setUp(self) -> None:
        self.user = sample_user()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for the authenticated user"""
        user_test = sample_user(
            email='test2@recipeapi.com',
            password='somethingrandom2'
        )

        Tag.objects.create(user=user_test, name='user_test')
        tag = Tag.objects.create(user=self.user, name='user')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering tags assigned to recipes"""
        tag_1 = Tag.objects.create(
            user=self.user,
            name='Vegan'
        )

        tag_2 = Tag.objects.create(
            user=self.user,
            name='Fish'
        )

        recipe = Recipe.objects.create(
            user=self.user,
            time_minutes=5,
            price=2.00,
            title='Fish and Fries'
        )

        recipe.tags.add(tag_2)

        res = self.client.get(
            TAGS_URL,
            {'assigned_only': 1}
        )

        serializer_1 = TagSerializer(tag_1)
        serializer_2 = TagSerializer(tag_2)

        self.assertNotIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
