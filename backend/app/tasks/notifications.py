"""Celery task for sending WhatsApp notifications."""
import httpx
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.notification_scheduler import NotificationScheduler
from app.config import settings


@celery_app.task(name="app.tasks.notifications.send_notifications")
def send_notifications():
    """Check for games needing notifications and send via OpenClaw."""
    db = SessionLocal()

    try:
        scheduler = NotificationScheduler(db)
        notifications = scheduler.get_games_needing_notification()

        sent_count = 0
        for notif in notifications:
            game = notif["game"]
            message = notif["message"]
            event_type = notif["event_type"]

            # Send WhatsApp notification via OpenClaw
            try:
                if settings.openclaw_api_url and settings.whatsapp_notification_number:
                    headers = {}
                    if settings.openclaw_api_token:
                        headers["Authorization"] = f"Bearer {settings.openclaw_api_token}"

                    response = httpx.post(
                        settings.openclaw_api_url,
                        json={
                            "to": settings.whatsapp_notification_number,
                            "message": message
                        },
                        headers=headers,
                        timeout=10.0
                    )

                    if response.status_code == 200:
                        # Mark notification as sent
                        scheduler.mark_notification_sent(game.id, event_type)
                        sent_count += 1
                    else:
                        print(f"Failed to send notification: {response.status_code}")
                else:
                    # No OpenClaw configured - just mark as sent (for testing)
                    scheduler.mark_notification_sent(game.id, event_type)
                    sent_count += 1

            except Exception as e:
                print(f"Error sending notification for game {game.id}: {e}")

        return {
            "success": True,
            "notifications_sent": sent_count
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
