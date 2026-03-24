from django.test import TestCase
from .models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


# Create your tests here.
class UserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user1",
            email="[EMAIL_ADDRESS]",
            password="password",
            role="user",
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, "user1")
        self.assertEqual(self.user.email, "[EMAIL_ADDRESS]")
        self.assertEqual(self.user.role, "user")

    def test_user_update(self):
        self.user.username = "user2"
        self.user.save()
        self.assertEqual(self.user.username, "user2")

    def test_user_delete(self):
        self.user.delete()
        self.assertEqual(User.objects.count(), 0)

    def test_user_detail(self):
        self.assertEqual(User.objects.get(user_id=self.user.user_id), self.user)

    def test_user_list(self):
        self.assertEqual(User.objects.count(), 1)

    def test_user_creation_with_invalid_data(self):
        with self.assertRaises(ValidationError):
            User.objects.create(
                username="user1",
                email="[EMAIL_ADDRESS]",
                password="password",
                role="user",
            )
