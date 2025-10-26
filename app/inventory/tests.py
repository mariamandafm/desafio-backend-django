from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import AutoPart
from inventory.serializers import AutoPartSerializer
from decimal import Decimal


AUTO_PART_URL = reverse('inventory:auto-part-list')


def detail_url(auto_part_id):
    return reverse('inventory:auto-part-detail', args=[auto_part_id])


def create_auto_part(**params):
    """Helper function to create and return a sample AutoPart."""
    defaults = {
        'name': 'Sample Part',
        'description': 'This is a sample auto part.',
        'price': 19.99,
        'stock_quantity': 100,
    }
    defaults.update(params)
    return AutoPart.objects.create(**defaults)


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def create_superuser(**params):
    return get_user_model().objects.create_superuser(**params)


class RegularUserAutoPartAPITests(TestCase):
    """Tests for authenticated non-admin user access to the AutoPart API."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(username="user", password="userpass123", email="user@testing.com")
        self.client.force_authenticate(self.user)

    def test_list_auto_parts(self):
        create_auto_part()
        create_auto_part(name='Another Part')
        auto_part_items = AutoPart.objects.all().order_by('id')
        serializer = AutoPartSerializer(auto_part_items, many=True)

        res = self.client.get(AUTO_PART_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_auto_parts_details(self):
        auto_part = create_auto_part()
        serializer = AutoPartSerializer(auto_part)

        res = self.client.get(detail_url(auto_part.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_cannot_create_auto_part(self):
        payload = {
            'name': 'Unauthorized Part',
            'description': 'Should not be created',
            'price': Decimal('29.99'),
            'stock_quantity': 50,
        }

        res = self.client.post(AUTO_PART_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_full_update_auto_part(self):
        auto_part = create_auto_part()
        payload = {
            'name': 'Unauthorized Part',
            'description': 'Should not be created',
            'price': Decimal('29.99'),
            'stock_quantity': 50,
        }

        res = self.client.put(detail_url(auto_part.id), payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_partial_update_auto_part(self):
        auto_part = create_auto_part()
        payload = {
            'price': Decimal('39.99'),
        }

        res = self.client.patch(detail_url(auto_part.id), payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_delete_auto_part(self):
        auto_part = create_auto_part()

        res = self.client.delete(detail_url(auto_part.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAutoPartAPITests(TestCase):
    """Tests for admin user access to the AutoPart API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_superuser(username="admin", password="adminpass123", email="admin@testing.com")
        self.client.force_authenticate(self.user)

    def test_create_auto_part(self):
        payload = {
            'name': 'Authorized Part',
            'description': 'Should be created',
            'price': Decimal('29.99'),
            'stock_quantity': 50,
        }

        res = self.client.post(AUTO_PART_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        auto_part = AutoPart.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(auto_part, k), v)

    def test_update_auto_part(self):
        auto_part = create_auto_part()
        payload = {
            'name': 'Updated Part',
            'description': 'This part has been updated.',
            'price': Decimal('39.99'),
            'stock_quantity': 75,
        }

        res = self.client.put(detail_url(auto_part.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        auto_part.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(auto_part, k), v)

    def test_partial_update_auto_part(self):
        auto_part = create_auto_part()
        payload = {
            'price': Decimal('49.99'),
        }

        res = self.client.patch(detail_url(auto_part.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        auto_part.refresh_from_db()
        self.assertEqual(auto_part.price, payload['price'])

    def test_delete_auto_part(self):
        auto_part = create_auto_part()

        res = self.client.delete(detail_url(auto_part.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AutoPart.objects.filter(id=auto_part.id).exists())
