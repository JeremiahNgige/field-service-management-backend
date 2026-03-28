from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from user.models import User
from jobs.models import Job

class JobLifecycleIntegrationTests(APITestCase):
    def setUp(self):
        # Admin creates jobs, technician works on them
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword",
            username="admin_user",
            phone_number="0000000001",
            user_type="admin",
            address="HQ"
        )
        self.technician = User.objects.create_user(
            email="tech@example.com",
            password="techpassword",
            username="tech_guy",
            phone_number="0000000002",
            user_type="technician",
            address="Field"
        )
        
        # URLs
        self.create_url = reverse("jobs:create")
        
        # We need token authentication to do requests
        response = self.client.post(reverse("user:login"), {
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        self.admin_token = response.data["access"]
        
        response = self.client.post(reverse("user:login"), {
            "email": "tech@example.com",
            "password": "techpassword"
        })
        self.tech_token = response.data["access"]

        # Valid Job Payload to use across tests
        self.start_time = timezone.now() + timedelta(days=1)
        self.end_time = timezone.now() + timedelta(days=1, hours=2)
        
        self.job_payload = {
            "title": "Fix HVAC System",
            "description": "The AC unit on the roof is leaking",
            "customer_name": "Acme Corp",
            "phone_number": "9876543210",
            "address": {"street": "123 Business Rd", "city": "Metropolis"},
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "price": "150.00",
            "currency": "USD",
            "priority": "high",
            "status": "unassigned" # It should start as unassigned
        }

    def test_job_create_assign_update_lifecycle(self):
        # 1. Admin creates a new unassigned job
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.post(self.create_url, self.job_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["job"]["status"], "unassigned")
        job_id = response.data["job"]["job_id"]
        
        update_url = reverse("jobs:update", kwargs={"job_id": job_id})
        detail_url = reverse("jobs:detail", kwargs={"job_id": job_id})

        # 2. Admin assigns the job to the technician
        assign_payload = {
            "assigned_to": self.technician.user_id
        }
        response = self.client.put(update_url, assign_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checking if status auto-updated to "assigned"
        self.assertEqual(response.data["job"]["status"], "assigned")
        self.assertEqual(str(response.data["job"]["assigned_to"]), str(self.technician.user_id))

        # 3. Technician updates the job status to 'in_progress'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tech_token}')
        progress_payload = {
            "status": "in_progress"
        }
        response = self.client.put(update_url, progress_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job"]["status"], "in_progress")
        
        # Check detail view
        response = self.client.get(detail_url)
        self.assertEqual(response.data["job"]["status"], "in_progress")

        # 4. Technician completes the job and uploads signature
        complete_payload = {
            "status": "completed",
            "signature": "https://example.com/signature.png"
        }
        response = self.client.put(update_url, complete_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job"]["status"], "completed")
        self.assertEqual(response.data["job"]["signature"], complete_payload["signature"])

class TechnicianWorkFlowIntegrationTests(APITestCase):
    def setUp(self):
        self.technician = User.objects.create_user(
            email="fieldtech@example.com",
            password="techpassword",
            username="tech_workflow",
            phone_number="1112223334",
            user_type="technician",
            address="Field Office"
        )
        
        response = self.client.post(reverse("user:login"), {
            "email": "fieldtech@example.com",
            "password": "techpassword"
        })
        self.tech_token = response.data["access"]
        
        # Create some jobs directly in DB
        self.start_time = timezone.now() + timedelta(days=1)
        self.end_time = timezone.now() + timedelta(days=1, hours=2)
        
        Job.objects.create(
            title="My Job 1",
            customer_name="Cust 1",
            phone_number="1234567890",
            address={"city": "A"},
            start_time=self.start_time,
            end_time=self.end_time,
            assigned_to=self.technician,
            status="assigned"
        )
        Job.objects.create(
            title="My Job 2",
            customer_name="Cust 2",
            phone_number="1234567890",
            address={"city": "B"},
            start_time=self.start_time,
            end_time=self.end_time,
            assigned_to=self.technician,
            status="assigned"
        )
        # Create unassigned job
        Job.objects.create(
            title="Unassigned Job",
            customer_name="Cust 3",
            phone_number="1234567890",
            address={"city": "C"},
            start_time=self.start_time,
            end_time=self.end_time,
            status="unassigned"
        )

    def test_fetch_assigned_jobs_and_sync_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tech_token}')
        
        # 1. Fetch assigned jobs
        fetch_jobs_url = reverse("user:fetch-assigned-jobs")
        response = self.client.get(fetch_jobs_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # With pagination, data is inside ['jobs']['results'] if configured custom, 
        # but our view returns `self.get_paginated_response(serializer.data)`
        # which usually yields `{ "next": ..., "previous": ..., "jobs": [...] }` or just results array
        jobs_list = response.data["jobs"] 
        
        # Verify Technician only sees 2 jobs
        self.assertEqual(len(jobs_list), 2)
        
        titles = [job["title"] for job in jobs_list]
        self.assertIn("My Job 1", titles)
        self.assertIn("My Job 2", titles)
        self.assertNotIn("Unassigned Job", titles)
        
        # 2. Update FCM Token
        fcm_url = reverse("user:update-fcm-token")
        fcm_payload = {
            "fcm_token": "abc_123_test_fcm_token_device_sync_mock"
        }
        
        response = self.client.put(fcm_url, fcm_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # DB Verify
        user_in_db = User.objects.get(email=self.technician.email)
        self.assertEqual(user_in_db.fcm_token, "abc_123_test_fcm_token_device_sync_mock")
