from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Task

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.payload = {
            'username': 'shreya',
            'email': 'shreya@example.com',
            'password': 'StrongPass#2026',
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.filter(username='shreya').exists())

    def test_register_duplicate_username(self):
        self.client.post(self.register_url, self.payload, format='json')
        other = {**self.payload, 'email': 'other@example.com'}
        response = self.client.post(self.register_url, other, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_register_duplicate_email(self):
        self.client.post(self.register_url, self.payload, format='json')
        other = {**self.payload, 'username': 'another'}
        response = self.client.post(self.register_url, other, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_weak_password(self):
        payload = {**self.payload, 'password': '123'}
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_returns_tokens(self):
        self.client.post(self.register_url, self.payload, format='json')
        response = self.client.post(
            self.login_url,
            {'username': 'shreya', 'password': 'StrongPass#2026'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        self.client.post(self.register_url, self.payload, format='json')
        response = self.client.post(
            self.login_url,
            {'username': 'shreya', 'password': 'wrong-password'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='shreya', email='shreya@example.com', password='StrongPass#2026'
        )
        self.other_user = User.objects.create_user(
            username='ravi', email='ravi@example.com', password='StrongPass#2026'
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('task-list')
        self.due_date = (timezone.localdate() + timedelta(days=7)).isoformat()
        self.task = Task.objects.create(
            owner=self.user,
            title='Write report',
            description='Quarterly report',
            due_date=self.due_date,
            priority='high',
            status='pending',
        )
        self.other_task = Task.objects.create(
            owner=self.other_user,
            title='Private task',
            due_date=self.due_date,
        )
        self.detail_url = reverse('task-detail', args=[self.task.id])
        self.other_detail_url = reverse('task-detail', args=[self.other_task.id])
        self.valid_payload = {
            'title': 'Plan sprint',
            'description': 'Sprint planning',
            'due_date': self.due_date,
            'priority': 'medium',
            'status': 'pending',
        }

    def test_create_task(self):
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Task.objects.get(id=response.data['id'])
        self.assertEqual(created.owner, self.user)
        self.assertEqual(created.title, 'Plan sprint')

    def test_list_returns_only_own_tasks(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Write report')

    def test_retrieve_task(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Write report')

    def test_cannot_retrieve_other_users_task(self):
        response = self.client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_task(self):
        payload = {**self.valid_payload, 'title': 'Write final report', 'status': 'completed'}
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Write final report')
        self.assertEqual(self.task.status, 'completed')

    def test_cannot_update_other_users_task(self):
        response = self.client.put(self.other_detail_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.title, 'Private task')

    def test_delete_task(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_cannot_delete_other_users_task(self):
        response = self.client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Task.objects.filter(id=self.other_task.id).exists())

    def test_create_with_blank_title(self):
        payload = {**self.valid_payload, 'title': '   '}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_create_with_past_due_date(self):
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        payload = {**self.valid_payload, 'due_date': past}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('due_date', response.data)

    def test_create_with_invalid_priority(self):
        payload = {**self.valid_payload, 'priority': 'urgent'}
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('priority', response.data)

    def test_create_with_missing_fields(self):
        response = self.client.post(self.list_url, {'description': 'No title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        self.assertIn('due_date', response.data)


class TaskAuthRequiredTests(APITestCase):
    def test_list_requires_authentication(self):
        response = self.client.get(reverse('task-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_authentication(self):
        response = self.client.post(reverse('task-list'), {'title': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)