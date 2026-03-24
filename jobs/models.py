from django.db import models
import uuid

# Create your models here.


class Job(models.Model):
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
    )
    requirements = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="jobs"
    )
    technician = models.ForeignKey(
        "user.User", on_delete=models.CASCADE, related_name="assigned_jobs"
    )
    phone_number = models.CharField(max_length=15)
    address = models.JSONField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    signature = models.URLField(blank=True, null=True)
    photos = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.title
