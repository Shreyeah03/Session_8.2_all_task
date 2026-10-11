from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Task

User = get_user_model()


class AuthAndTaskTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", "alice@example.com", "Str0ng-pass-1")
        self.bob = User.objects.create_user("bob", "bob@example.com", "Str0ng-pass-2")
        self.today = timezone.localdate()

    def login(self, username, password):
        res = self.client.post(reverse("login-api"), {"username": username, "password": password})
        self.assertEqual(res.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_register_returns_tokens(self):
        res = self.client.post(reverse("register-api"), {
            "username": "carol", "email": "carol@example.com",
            "password": "Str0ng-pass-3", "confirm_password": "Str0ng-pass-3",
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn("access", res.data)

    def test_register_password_mismatch(self):
        res = self.client.post(reverse("register-api"), {
            "username": "carol", "email": "carol@example.com",
            "password": "Str0ng-pass-3", "confirm_password": "nope",
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("confirm_password", res.data)

    def test_tasks_require_auth(self):
        self.assertEqual(self.client.get("/api/tasks/").status_code, 401)

    def test_users_only_see_their_own_tasks(self):
        Task.objects.create(user=self.alice, title="Alice task", due_date=self.today)
        Task.objects.create(user=self.bob, title="Bob task", due_date=self.today)
        self.login("alice", "Str0ng-pass-1")
        res = self.client.get("/api/tasks/")
        self.assertEqual([t["title"] for t in res.data], ["Alice task"])
        bob_task = Task.objects.get(user=self.bob)
        self.assertEqual(self.client.get(f"/api/tasks/{bob_task.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/tasks/{bob_task.id}/").status_code, 404)

    def test_crud_complete_filter_sort(self):
        self.login("alice", "Str0ng-pass-1")
        later = self.today + timedelta(days=5)
        res = self.client.post("/api/tasks/", {"title": "Later", "priority": "low", "due_date": later})
        self.assertEqual(res.status_code, 201)
        late_id = res.data["id"]
        self.client.post("/api/tasks/", {"title": "Soon report", "priority": "high", "due_date": self.today})

        titles = [t["title"] for t in self.client.get("/api/tasks/").data]
        self.assertEqual(titles, ["Soon report", "Later"])  # due date ascending

        self.assertEqual(len(self.client.get("/api/tasks/?priority=high").data), 1)
        self.assertEqual(len(self.client.get("/api/tasks/?search=report").data), 1)

        self.assertEqual(self.client.post(f"/api/tasks/{late_id}/complete/").data["status"], "completed")
        self.assertEqual(len(self.client.get("/api/tasks/?status=completed").data), 1)
        self.assertEqual(len(self.client.get("/api/tasks/?status=pending").data), 1)

        res = self.client.patch(f"/api/tasks/{late_id}/", {"title": "Renamed"})
        self.assertEqual(res.data["title"], "Renamed")
        self.assertEqual(self.client.delete(f"/api/tasks/{late_id}/").status_code, 204)

    def test_validation_errors(self):
        self.login("alice", "Str0ng-pass-1")
        res = self.client.post("/api/tasks/", {"title": "  ", "due_date": self.today - timedelta(days=1)})
        self.assertEqual(res.status_code, 400)
        self.assertIn("title", res.data)
        self.assertIn("due_date", res.data)
