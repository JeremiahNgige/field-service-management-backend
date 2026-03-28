from django.db import models
import uuid

# Create your models here.


class Job(models.Model):
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    customer_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ("unassigned", "Unassigned"),
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="unassigned",
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        default="medium",
    )
    requirements = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="assigned_jobs",
        null=True,
        blank=True,
    )
    is_paid = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15)
    address = models.JSONField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    signature = models.URLField(blank=True, null=True)
    photos = models.JSONField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        status_changed_to_assigned = False

        if self.assigned_to is not None and self.status == "unassigned":
            self.status = "assigned"

        if not is_new and self._original_status == "unassigned" and self.status == "assigned":
            status_changed_to_assigned = True

        super().save(*args, **kwargs)

        if status_changed_to_assigned:
            from .signals import post_assigned
            post_assigned.send(sender=self.__class__, instance=self)

        self._original_status = self.status

    @property
    def is_overdue(self):
        from django.utils import timezone

        if self.status in ["completed", "cancelled"]:
            return False
        return timezone.now() > self.end_time
