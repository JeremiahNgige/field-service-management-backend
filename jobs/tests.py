from django.test import TestCase
from .models import Job
from django.utils import timezone
from django.core.exceptions import ValidationError


# Create your tests here.
class JobTests(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Job 1",
            description="Description 1",
            status="pending",
            priority="low",
            requirements={"key": "value"},
            phone_number="1234567890",
            address={"key": "value"},
            start_time=timezone.now(),
            end_time=timezone.now(),
            signature="http://example.com/signature.png",
            photos=["http://example.com/photo.png"],
        )

    def test_job_creation(self):
        self.assertEqual(self.job.title, "Job 1")
        self.assertEqual(self.job.description, "Description 1")
        self.assertEqual(self.job.status, "pending")
        self.assertEqual(self.job.priority, "low")
        self.assertEqual(self.job.requirements, {"key": "value"})
        self.assertEqual(self.job.phone_number, "1234567890")
        self.assertEqual(self.job.address, {"key": "value"})
        self.assertEqual(self.job.start_time, timezone.now())
        self.assertEqual(self.job.end_time, timezone.now())
        self.assertEqual(self.job.signature, "http://example.com/signature.png")
        self.assertEqual(self.job.photos, ["http://example.com/photo.png"])

    def test_job_update(self):
        self.job.title = "Job 2"
        self.job.save()
        self.assertEqual(self.job.title, "Job 2")

    def test_job_delete(self):
        self.job.delete()
        self.assertEqual(Job.objects.count(), 0)

    def test_job_detail(self):
        self.assertEqual(Job.objects.get(job_id=self.job.job_id), self.job)

    def test_job_list(self):
        self.assertEqual(Job.objects.count(), 1)

    def test_job_creation_with_invalid_data(self):
        with self.assertRaises(ValidationError):
            Job.objects.create(
                title="Job 1",
                description="Description 1",
                status="pending",
                priority="low",
                requirements={"key": "value"},
                phone_number="1234567890",
                address={"key": "value"},
                start_time=timezone.now(),
                end_time=timezone.now(),
                signature="http://example.com/signature.png",
                photos=["http://example.com/photo.png"],
            )
