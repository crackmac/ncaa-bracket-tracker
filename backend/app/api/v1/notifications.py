from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Bracket
from app.services.notifier import notifier

router = APIRouter()


class NotificationResponse(BaseModel):
    """Notification response model."""

    success: bool
    message: str


@router.post("/notify", response_model=NotificationResponse)
async def send_test_notification(db: Session = Depends(get_db)):
    """
    Send a test WhatsApp notification.
    Useful for verifying OpenClaw integration.
    """
    message = "🏀 NCAA Bracket Tracker Test Notification\n\n"
    message += "This is a test message from your bracket tracker.\n"
    message += "OpenClaw integration is working!"

    success = await notifier.send_whatsapp_message(message)

    if success:
        return NotificationResponse(success=True, message="Test notification sent successfully")
    else:
        return NotificationResponse(
            success=False, message="Failed to send notification - check OpenClaw configuration"
        )


@router.post("/notify/bracket/{bracket_id}", response_model=NotificationResponse)
async def notify_bracket_score(bracket_id: int, db: Session = Depends(get_db)):
    """
    Send a notification with current bracket score.

    Args:
        bracket_id: The bracket ID to send notification for.
    """
    bracket = db.query(Bracket).filter(Bracket.id == bracket_id).first()
    if not bracket:
        return NotificationResponse(success=False, message=f"Bracket {bracket_id} not found")

    # Calculate pick stats
    picks = bracket.picks
    correct = sum(1 for p in picks if p.is_correct is True)

    success = await notifier.notify_bracket_score(
        bracket=bracket, total_points=bracket.total_points, correct_picks=correct, total_picks=len(picks)
    )

    if success:
        return NotificationResponse(success=True, message=f"Bracket score notification sent for {bracket.name}")
    else:
        return NotificationResponse(success=False, message="Failed to send notification")
