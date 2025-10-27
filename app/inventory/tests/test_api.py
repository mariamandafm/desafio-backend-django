from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from core.models import AutoPart
from inventory.serializers import AutoPartSerializer
from decimal import Decimal


AUTO_PART_URL = reverse('inventory:auto-part-list')
CSV_UPLOAD_URL = reverse('inventory:auto-part-upload-csv')


def detail_url(auto_part_id):
    return reverse('inventory:auto-part-detail', args=[auto_part_id])


def create_auto_part(**params):
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


class AnonymousUserAutoPartAPITests(TestCase):
    """Tests for unauthenticated access to the AutoPart API."""

    def setUp(self):
        self.client = APIClient()

    def test_cannot_list_auto_parts(self):
        res = self.client.get(AUTO_PART_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_retrieve_auto_part_details(self):
        auto_part = create_auto_part()

        res = self.client.get(detail_url(auto_part.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_auto_part(self):
        res = self.client.post(AUTO_PART_URL, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_full_update_auto_part(self):
        res = self.client.put(detail_url(1), {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_partial_update_auto_part(self):
        res = self.client.patch(detail_url(1), {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_delete_auto_part(self):
        res = self.client.delete(detail_url(1))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_bulk_create_auto_parts_via_csv(self):
        res = self.client.post(CSV_UPLOAD_URL, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


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
        res = self.client.post(AUTO_PART_URL, {})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_full_update_auto_part(self):
        res = self.client.put(detail_url(1), {})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_partial_update_auto_part(self):
        res = self.client.patch(detail_url(1), {})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_delete_auto_part(self):
        res = self.client.delete(detail_url(1))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_bulk_create_auto_parts_via_csv(self):
        res = self.client.post(CSV_UPLOAD_URL, {})

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

    def test_bulk_create_auto_parts_via_csv_no_file(self):
        res = self.client.post(CSV_UPLOAD_URL, {})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    def test_bulk_create_auto_parts_via_csv_invalid_file_type(self):
        invalid_file = SimpleUploadedFile("partes.txt", b"Invalid content", content_type="text/plain")
        data = {"file": invalid_file}

        res = self.client.post(CSV_UPLOAD_URL, data, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    def test_bulk_create_auto_parts_via_csv_decode_error(self):
        invalid_content = b'\xff\xfe\x00\x00'
        invalid_file = SimpleUploadedFile("partes.csv", invalid_content, content_type="text/csv")
        data = {"file": invalid_file}

        res = self.client.post(CSV_UPLOAD_URL, data, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    @patch('inventory.views.import_auto_parts_from_csv.delay')
    def test_bulk_create_auto_parts_via_csv(self, mock_import_task):
        csv_content = (
            b"nome,descricao,preco,quantidade_inicial\n"
            b"Part X,Description X,12.50,10\n"
            b"Part Y,Description Y,22.75,20\n"
            b"Part Z,Description Z,32.00,30\n"
        )
        csv_file = SimpleUploadedFile("partes.csv", csv_content, content_type="text/csv")
        data = {"file": csv_file}

        res = self.client.post(CSV_UPLOAD_URL, data, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('message', res.data)
        mock_import_task.assert_called_once()
