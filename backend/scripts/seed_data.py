"""Seed database with sample tournament data."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import Base
from app.db.models import Bracket, Game, Pick, Team, Tournament, User
from app.db.session import engine
from scripts.load_tournament import load_tournament


def seed_database():
    """Seed database with sample data."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Seeding data...")
    session = Session(bind=engine)

    try:
        # Create user
        user = User(
            name="Demo User",
            email="demo@example.com",
        )
        session.add(user)
        session.commit()
        print(f"✓ Created user: {user.email}")

        # Load tournament from YAML
        yaml_path = Path(__file__).parent.parent / "data" / "tournaments" / "2026.yaml"
        tournament_id, teams, games = load_tournament(yaml_path, session)
        print(f"✓ Loaded tournament: {teams} teams, {games} games")

        # Get tournament
        tournament = session.get(Tournament, tournament_id)

        # Create sample bracket with picks for first 4 games
        bracket = Bracket(
            user_id=user.id,
            tournament_id=tournament.id,
            name="Championship Run",
            bracket_type="balanced",
            total_points=0,
            possible_points=0,
        )
        session.add(bracket)
        session.commit()
        print(f"✓ Created bracket: {bracket.name}")

        # Create picks for first few games (for demo)
        first_games = session.query(Game).filter(
            Game.tournament_id == tournament.id,
            Game.round == "Round 64"
        ).limit(4).all()

        for game in first_games:
            # Predict higher seed wins
            home_team = session.get(Team, game.home_team_id)
            away_team = session.get(Team, game.away_team_id)
            predicted_winner_id = home_team.id if home_team.seed < away_team.seed else away_team.id

            pick = Pick(
                bracket_id=bracket.id,
                game_id=game.id,
                predicted_winner_id=predicted_winner_id,
                points_value=10,  # Round 64
                points_earned=0,
            )
            session.add(pick)

        session.commit()
        print(f"✓ Created {len(first_games)} sample picks")

        # Calculate bracket scores
        from app.services.scoring_engine import ScoringEngine
        engine_service = ScoringEngine(session)
        scores = engine_service.calculate_bracket_score(bracket.id)
        print(f"✓ Calculated bracket scores: {scores}")

        print("\n✅ Database seeded successfully!")
        print(f"\nSummary:")
        print(f"  - User: {user.email}")
        print(f"  - Tournament: {tournament.name}")
        print(f"  - Teams: {teams}")
        print(f"  - Games: {games}")
        print(f"  - Bracket: {bracket.name}")
        print(f"  - Total Points: {bracket.total_points}")
        print(f"  - Possible Points: {bracket.possible_points}")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("NCAA Bracket Tracker - Database Seeder")
    print("=" * 50)
    seed_database()
