from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User

class AuthProfileIntegrationTests(APITestCase):
    def setUp(self):
        # We need to use reverse to find the URLs safely or hardcode if we know them
        # user urls seem to be app_name = "user", names="register", "login", "profile", "update"
        self.register_url = reverse("user:register")
        self.login_url = reverse("user:login")
        self.profile_url = reverse("user:profile")
        self.update_url = reverse("user:update")

        self.user_data = {
            "username": "technician_dave",
            "email": "dave.tech@example.com",
            "phone_number": "1234567890",
            "address": "123 Main St, Springfield",
            "user_type": "technician",
            "password": "SecurePassword123!",
            "password2": "SecurePassword123!"
        }

    def test_complete_auth_profile_flow(self):
        # 1. Register a new technician
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])
        user_id = response.data["user"]["user_id"]

        # Ensure password wasn't returned
        self.assertNotIn("password", response.data["user"])

        # 2. Login to retrieve JWT tokens
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        
        access_token = response.data["access"]
        
        # Authenticate all subsequent requests with the JWT
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 3. Fetch user profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], self.user_data["username"])
        self.assertEqual(response.data["user"]["user_id"], user_id)

        # 4. Update profile details
        update_data = {
            "address": "456 Advanced Ave, Metropolis"
        }
        response = self.client.put(self.update_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["address"], update_data["address"])

        # DB Verify
        user_in_db = User.objects.get(email=self.user_data["email"])
        self.assertEqual(user_in_db.address, update_data["address"])

    def test_registration_validation_errors(self):
        """Ensure clear validation errors are returned for bad inputs based on our recent refactor"""
        bad_data = self.user_data.copy()
        bad_data["password2"] = "Mismatch!"
        
        response = self.client.post(self.register_url, bad_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data["message"])

    def test_login_invalid_credentials(self):
        login_data = {
            "email": "not_real@example.com",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No account found", response.data["message"])
