"""Sync service for updating game data from ESPN."""
from typing import Any
from sqlalchemy.orm import Session

from app.db.models import Game, Bracket


class SyncService:
    """Service for syncing game data from ESPN."""

    def __init__(self, db: Session, espn_client: Any, scoring_engine_class: Any):
        """Initialize sync service.

        Args:
            db: Database session
            espn_client: ESPN API client instance
            scoring_engine_class: ScoringEngine class (not instance) for score calculation
        """
        self.db = db
        self.espn_client = espn_client
        self.scoring_engine_class = scoring_engine_class

    async def sync_games(self) -> dict:
        """Sync game data from ESPN API.

        Returns:
            Dict with games_updated and brackets_updated counts
        """
        games_updated = 0

        try:
            # Fetch today's games from ESPN
            events = await self.espn_client.get_tournament_games()

            for event in events:
                for competition in event.competitions:
                    # Find game in database by ESPN ID
                    game = self.db.query(Game).filter(Game.espn_id == event.id).first()

                    if game:
                        # Update game scores and status
                        if len(competition.competitors) >= 2:
                            home_competitor = next(
                                (c for c in competition.competitors if c.homeAway == "home"),
                                None
                            )
                            away_competitor = next(
                                (c for c in competition.competitors if c.homeAway == "away"),
                                None
                            )

                            if home_competitor and home_competitor.score:
                                game.home_score = int(home_competitor.score)

                            if away_competitor and away_competitor.score:
                                game.away_score = int(away_competitor.score)

                            # Update status
                            status_type = competition.status.get("type", {}).get("name", "")
                            if status_type == "STATUS_FINAL":
                                game.status = "completed"
                            elif status_type == "STATUS_IN_PROGRESS":
                                game.status = "in_progress"
                            else:
                                game.status = "scheduled"

                            games_updated += 1

            self.db.commit()

            # Recalculate all bracket scores
            brackets = self.db.query(Bracket).all()
            brackets_updated = 0

            for bracket in brackets:
                engine = self.scoring_engine_class(self.db)
                engine.calculate_bracket_score(bracket.id)
                brackets_updated += 1

            return {
                "games_updated": games_updated,
                "brackets_updated": brackets_updated
            }

        except Exception as e:
            self.db.rollback()
            raise
