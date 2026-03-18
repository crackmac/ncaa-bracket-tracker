import logging
from sqlalchemy.orm import Session

from app.db.models import Bracket, Game, Pick, Team

logger = logging.getLogger("app.scoring_engine")

# ESPN Tournament Challenge scoring
ROUND_POINTS = {
    "Round 64": 10,
    "Round 32": 20,
    "Sweet 16": 40,
    "Elite 8": 80,
    "Final Four": 160,
    "Championship": 320,
}


class ScoringEngine:
    """Scoring engine for calculating bracket points."""

    def __init__(self, db: Session):
        self.db = db

    def get_points_for_round(self, round_name: str) -> int:
        """Get point value for a given round."""
        return ROUND_POINTS.get(round_name, 10)

    def is_upset(self, game: Game) -> bool:
        """
        Determine if a game result is an upset.
        An upset occurs when a lower-seeded team (higher number) beats a higher-seeded team.
        """
        if game.status != "completed" or game.home_score is None or game.away_score is None:
            return False

        winner_id = game.home_team_id if game.home_score > game.away_score else game.away_team_id
        loser_id = game.away_team_id if game.home_score > game.away_score else game.home_team_id

        winner = self.db.query(Team).filter(Team.id == winner_id).first()
        loser = self.db.query(Team).filter(Team.id == loser_id).first()

        if winner and loser:
            # Higher seed number = lower seed (e.g., 16 seed is lower than 1 seed)
            return winner.seed > loser.seed

        return False

    def calculate_bracket_score(self, bracket_id: int) -> dict[str, int]:
        """
        Calculate total score for a bracket.

        Returns:
            Dictionary with total_points, correct_picks, total_picks, and possible_points.
        """
        logger.debug(f"Calculating score for bracket {bracket_id}")
        bracket = self.db.query(Bracket).filter(Bracket.id == bracket_id).first()
        if not bracket:
            raise ValueError(f"Bracket {bracket_id} not found")

        total_points = 0
        correct_picks = 0
        total_picks = 0
        possible_points = 0

        picks = self.db.query(Pick).filter(Pick.bracket_id == bracket_id).all()

        for pick in picks:
            game = pick.game
            total_picks += 1

            # Calculate points value for this pick
            pick.points_value = self.get_points_for_round(game.round)

            # Check if game is completed
            if game.status == "completed" and game.home_score is not None and game.away_score is not None:
                # Determine actual winner
                actual_winner_id = game.home_team_id if game.home_score > game.away_score else game.away_team_id

                # Check if pick was correct
                if pick.predicted_winner_id == actual_winner_id:
                    pick.is_correct = True
                    pick.points_earned = pick.points_value
                    total_points += pick.points_earned
                    correct_picks += 1
                else:
                    pick.is_correct = False
                    pick.points_earned = 0

                # Update game upset status
                game.is_upset = self.is_upset(game)
            else:
                # Game not yet decided - still possible to earn these points
                possible_points += pick.points_value

        # Update bracket totals
        bracket.total_points = total_points
        bracket.possible_points = total_points + possible_points

        self.db.commit()

        logger.info(f"Bracket {bracket_id} score: {total_points}/{bracket.possible_points}")
        return {
            "total_points": total_points,
            "correct_picks": correct_picks,
            "total_picks": total_picks,
            "possible_points": bracket.possible_points,
        }

    def get_bracket_health(self, bracket_id: int) -> dict[str, any]:
        """
        Calculate bracket health metrics.

        Returns:
            Dictionary with current score, max possible, and health percentage.
        """
        scores = self.calculate_bracket_score(bracket_id)

        # Calculate maximum possible points (all remaining picks correct)
        max_possible = scores["possible_points"]

        # Calculate health percentage (current + possible / theoretical max)
        # Theoretical max is if all 63 games were worth their round value
        theoretical_max = sum(ROUND_POINTS.values()) * 10  # Rough estimate

        health_percentage = (max_possible / theoretical_max * 100) if theoretical_max > 0 else 0

        return {
            "current_points": scores["total_points"],
            "max_possible_points": max_possible,
            "health_percentage": round(health_percentage, 2),
            "correct_picks": scores["correct_picks"],
            "total_picks": scores["total_picks"],
            "accuracy": round(scores["correct_picks"] / scores["total_picks"] * 100, 2)
            if scores["total_picks"] > 0
            else 0,
        }
