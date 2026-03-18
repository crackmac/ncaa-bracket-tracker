"""Notification scheduler for determining which notifications to send."""
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Game, Bracket


class NotificationScheduler:
    """Determines which games need notifications."""

    def __init__(self, db: Session):
        self.db = db

    def get_games_needing_notification(self) -> List[Dict[str, Any]]:
        """Get list of games that need notifications sent.

        Returns:
            List of dicts with game info and notification type
        """
        notifications = []

        # Get all games
        stmt = select(Game)
        games = self.db.execute(stmt).scalars().all()

        for game in games:
            # Game starting soon (status is scheduled but no notification sent)
            if game.status == "scheduled" and game.last_notified_event is None:
                notifications.append({
                    "game": game,
                    "event_type": "game_start",
                    "message": f"🏀 Game starting: {game.home_team_name} vs {game.away_team_name}"
                })

            # Game in progress (no in_progress notification sent yet)
            elif game.status == "in_progress" and game.last_notified_event != "in_progress":
                notifications.append({
                    "game": game,
                    "event_type": "halftime",
                    "message": f"⏱️ Halftime: {game.home_team_name} {game.home_score} - {game.away_score} {game.away_team_name}"
                })

            # Game completed (no final notification sent)
            elif game.status == "completed" and game.last_notified_event != "completed":
                # Check for upset
                is_upset = self._is_upset(game)
                if is_upset:
                    notifications.append({
                        "game": game,
                        "event_type": "upset",
                        "message": f"🚨 UPSET! {game.home_team_name if game.home_score > game.away_score else game.away_team_name} wins!"
                    })
                else:
                    notifications.append({
                        "game": game,
                        "event_type": "game_final",
                        "message": f"✅ Final: {game.home_team_name} {game.home_score} - {game.away_score} {game.away_team_name}"
                    })

        return notifications

    def _is_upset(self, game: Game) -> bool:
        """Determine if game result is an upset (lower seed won).

        Args:
            game: Completed game

        Returns:
            True if lower seed won
        """
        if game.home_score is None or game.away_score is None:
            return False

        # Home team won
        if game.home_score > game.away_score:
            # Upset if home seed is higher (worse) than away seed
            return game.home_team_seed > game.away_team_seed
        else:
            # Away team won - upset if away seed is higher (worse)
            return game.away_team_seed > game.home_team_seed

    def mark_notification_sent(self, game_id: int, event_type: str) -> None:
        """Mark that a notification has been sent for a game.

        Args:
            game_id: Game ID
            event_type: Type of notification sent
        """
        stmt = select(Game).where(Game.id == game_id)
        game = self.db.execute(stmt).scalar_one_or_none()

        if game:
            game.last_notified_event = event_type
            self.db.commit()
