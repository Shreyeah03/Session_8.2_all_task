from django.test import TestCase

# Create your tests here.
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Product


class ProductAPITests(APITestCase):
    def setUp(self):
        self.list_url = reverse('product-list')
        self.product = Product.objects.create(
            name='Laptop',
            description='14 inch laptop',
            price=Decimal('55000.00'),
            stock_quantity=10,
            category='Electronics',
        )
        self.detail_url = reverse('product-detail', args=[self.product.id])
        self.valid_payload = {
            'name': 'Headphones',
            'description': 'Wireless headphones',
            'price': '2499.00',
            'stock_quantity': 25,
            'category': 'Accessories',
        }

    def test_create_product(self):
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(response.data['name'], 'Headphones')

    def test_list_products(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_product(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Laptop')
        self.assertEqual(Decimal(response.data['price']), Decimal('55000.00'))

    def test_retrieve_missing_product(self):
        url = reverse('product-detail', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        payload = {
            'name': 'Laptop Pro',
            'description': '16 inch laptop',
            'price': '75000.00',
            'stock_quantity': 5,
            'category': 'Electronics',
        }
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Laptop Pro')
        self.assertEqual(self.product.price, Decimal('75000.00'))
        self.assertEqual(self.product.stock_quantity, 5)

    def test_delete_product(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_create_with_negative_price(self):
        payload = {**self.valid_payload, 'price': '-10.00'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertEqual(Product.objects.count(), 1)

    def test_create_with_zero_price(self):
        payload = {**self.valid_payload, 'price': '0'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_create_with_negative_stock(self):
        payload = {**self.valid_payload, 'stock_quantity': -5}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock_quantity', response.data)

    def test_create_with_missing_fields(self):
        response = self.client.post(self.list_url, {'description': 'No name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('price', response.data)
        self.assertIn('category', response.data)

    def test_update_with_invalid_price(self):
        payload = {**self.valid_payload, 'price': '-1'}
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('55000.00'))