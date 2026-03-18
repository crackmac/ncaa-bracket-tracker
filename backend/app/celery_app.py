"""Celery application instance."""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "bracket_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.polling", "app.tasks.notifications"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Configure Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "poll-espn-every-5-minutes": {
        "task": "app.tasks.polling.poll_espn_data",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "send-notifications-every-10-minutes": {
        "task": "app.tasks.notifications.send_notifications",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
}
