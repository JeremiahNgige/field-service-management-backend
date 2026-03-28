from django.dispatch import Signal, receiver

post_assigned = Signal()

@receiver(post_assigned)
def trigger_assigned_notification(sender, instance, **kwargs):
    if instance.assigned_to and instance.assigned_to.fcm_token:
        from .tasks import send_fcm_notification_task
        from django.db import transaction
        transaction.on_commit(lambda: send_fcm_notification_task.delay(
            job_id=str(instance.job_id),
            user_id=str(instance.assigned_to.user_id),
            job_title=instance.title,
            end_time=instance.end_time.isoformat(),
            fcm_token=instance.assigned_to.fcm_token,
        ))
