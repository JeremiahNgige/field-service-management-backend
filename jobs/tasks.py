from celery import shared_task
import firebase_admin
from firebase_admin import messaging

@shared_task
def send_fcm_notification_task(job_id, user_id, job_title, end_time, fcm_token):
    if not firebase_admin._apps:
        print("Firebase is not initialized. Skipping notification.")
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title="New Job Assigned",
            body=f"You've been assigned {job_title} which ends at {end_time}",
        ),
        data={
            "job_id": str(job_id),
            "user_id": str(user_id),
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "type": "job_assigned"
        },
        token=fcm_token,
    )

    try:
        response = messaging.send(message)
        print(f"Successfully sent FCM notification: {response}")
    except Exception as e:
        print(f"Failed to send FCM notification: {e}")
