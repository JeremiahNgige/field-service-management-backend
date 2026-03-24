from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    user_id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user_type = models.CharField(
        max_length=50,
        choices=[
            ("admin", "Admin"),
            ("technician", "Technician"),
            ("customer", "Customer"),
        ],
    )
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.CharField(max_length=255)
    profile_picture = models.URLField(blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    last_login = models.DateTimeField(default=timezone.now)

    # Use email for login instead of username since username is no longer unique
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email if self.email else str(self.user_id)
