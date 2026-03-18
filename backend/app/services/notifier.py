import httpx

from app.config import settings
from app.db.models import Bracket, Game, Team


class NotificationService:
    """Service for sending WhatsApp notifications via OpenClaw."""

    def __init__(self):
        self.api_url = settings.openclaw_api_url
        self.api_token = settings.openclaw_api_token
        self.notification_number = settings.whatsapp_notification_number

    async def send_whatsapp_message(self, message: str) -> bool:
        """
        Send a WhatsApp message via OpenClaw API.

        Args:
            message: The message text to send.

        Returns:
            True if successful, False otherwise.
        """
        if not self.api_url or not self.notification_number:
            print("OpenClaw not configured - skipping notification")
            return False

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "to": self.notification_number,
                    "message": message,
                }

                headers = {}
                if self.api_token:
                    headers["Authorization"] = f"Bearer {self.api_token}"

                response = await client.post(self.api_url, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()

                print(f"WhatsApp notification sent successfully")
                return True

        except Exception as e:
            print(f"Failed to send WhatsApp notification: {e}")
            return False

    def format_game_result(self, game: Game, home_team: Team, away_team: Team) -> str:
        """
        Format a game result message.

        Args:
            game: The completed game.
            home_team: Home team.
            away_team: Away team.

        Returns:
            Formatted message string.
        """
        if game.home_score is None or game.away_score is None:
            return ""

        winner = home_team if game.home_score > game.away_score else away_team
        loser = away_team if game.home_score > game.away_score else home_team
        winner_score = max(game.home_score, game.away_score)
        loser_score = min(game.home_score, game.away_score)

        message = f"🏀 {game.round} - {game.region}\n"
        message += f"{winner.name} ({winner.seed}) defeats {loser.name} ({loser.seed})\n"
        message += f"Final Score: {winner_score}-{loser_score}"

        if game.is_upset:
            message += f"\n\n🚨 UPSET ALERT! #{winner.seed} {winner.name} over #{loser.seed} {loser.name}"

        return message

    def format_bracket_update(self, bracket: Bracket, total_points: int, correct_picks: int, total_picks: int) -> str:
        """
        Format a bracket score update message.

        Args:
            bracket: The bracket.
            total_points: Total points earned.
            correct_picks: Number of correct picks.
            total_picks: Total picks made.

        Returns:
            Formatted message string.
        """
        accuracy = round(correct_picks / total_picks * 100, 1) if total_picks > 0 else 0

        message = f"📊 Bracket Update: {bracket.name}\n\n"
        message += f"Points: {total_points}\n"
        message += f"Correct Picks: {correct_picks}/{total_picks} ({accuracy}%)\n"
        message += f"Max Possible: {bracket.possible_points}"

        return message

    async def notify_game_completed(self, game: Game, home_team: Team, away_team: Team) -> bool:
        """
        Send notification when a game is completed.

        Args:
            game: The completed game.
            home_team: Home team.
            away_team: Away team.

        Returns:
            True if successful, False otherwise.
        """
        message = self.format_game_result(game, home_team, away_team)
        return await self.send_whatsapp_message(message)

    async def notify_bracket_score(
        self, bracket: Bracket, total_points: int, correct_picks: int, total_picks: int
    ) -> bool:
        """
        Send notification with bracket score update.

        Args:
            bracket: The bracket.
            total_points: Total points earned.
            correct_picks: Number of correct picks.
            total_picks: Total picks made.

        Returns:
            True if successful, False otherwise.
        """
        message = self.format_bracket_update(bracket, total_points, correct_picks, total_picks)
        return await self.send_whatsapp_message(message)


# Global notifier instance
notifier = NotificationService()
