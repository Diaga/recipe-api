from django.test import TestCase, Client

from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self) -> None:
        """Setup function for AdminSiteTests"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@recipeapi.com",
            password="somethingrandom"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="user@recipeapi.com",
            password="somethingrandom"
        )

    def test_user_listed(self):
        """Tests that users are listed on user list page"""
        url = reverse("admin:core_user_changelist")
        response = self.client.get(url)

        self.assertContains(response, self.user.email)

    def test_user_change_page(self):
        """Tests that user edit page renders"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_add_page(self):
        """Tests that user add page renders"""
        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
