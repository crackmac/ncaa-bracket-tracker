"""Seed database with sample tournament data."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import Base
from app.db.models import Bracket, Game, Pick, Team, Tournament, User
from app.db.session import engine

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

        # Create tournament
        tournament = Tournament(
            year=2026,
            name="NCAA March Madness 2026",
            start_date=datetime(2026, 3, 17),
            end_date=datetime(2026, 4, 6),
        )
        session.add(tournament)
        session.commit()
        print(f"✓ Created tournament: {tournament.name}")

        # Create teams (East region sample)
        teams_data = [
            ("Duke", 1, "East", "duke_001"),
            ("Hampton", 16, "East", "hampton_016"),
            ("Memphis", 8, "East", "memphis_008"),
            ("Missouri", 9, "East", "missouri_009"),
            # West region sample
            ("Kansas", 4, "West", "kansas_004"),
            ("Iona", 13, "West", "iona_013"),
            ("Gonzaga", 2, "West", "gonzaga_002"),
            ("Norfolk State", 15, "West", "norfolk_015"),
        ]

        teams = []
        for name, seed, region, espn_id in teams_data:
            team = Team(
                tournament_id=tournament.id,
                name=name,
                seed=seed,
                region=region,
                espn_id=espn_id,
            )
            session.add(team)
            teams.append(team)

        session.commit()
        print(f"✓ Created {len(teams)} teams")

        # Create games
        games_data = [
            # East region - Round 64
            (0, 1, "Round 64", "East", "game_001", 78, 62, "completed"),  # Duke vs Hampton
            (2, 3, "Round 64", "East", "game_002", 71, 75, "completed"),  # Memphis vs Missouri (upset)
            # West region - Round 64
            (4, 5, "Round 64", "West", "game_003", 82, 68, "in_progress"),  # Kansas vs Iona
            (6, 7, "Round 64", "West", "game_004", None, None, "scheduled"),  # Gonzaga vs Norfolk State
        ]

        games = []
        for home_idx, away_idx, round_name, region, espn_id, home_score, away_score, status in games_data:
            home_team = teams[home_idx]
            away_team = teams[away_idx]

            game = Game(
                tournament_id=tournament.id,
                espn_id=espn_id,
                round=round_name,
                region=region,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=home_score,
                away_score=away_score,
                status=status,
                scheduled_time=datetime.utcnow() + timedelta(hours=2),
                completed_at=datetime.utcnow() if status == "completed" else None,
                is_upset=False,
            )

            # Check for upset
            if status == "completed" and home_score is not None and away_score is not None:
                winner_team = home_team if home_score > away_score else away_team
                loser_team = away_team if home_score > away_score else home_team
                if winner_team.seed > loser_team.seed:
                    game.is_upset = True

            session.add(game)
            games.append(game)

        session.commit()
        print(f"✓ Created {len(games)} games")

        # Create bracket
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

        # Create picks for each game
        picks_data = [
            (0, 0, 10),  # Duke (correct)
            (1, 2, 10),  # Memphis (incorrect - Missouri won)
            (2, 4, 10),  # Kansas (in progress)
            (3, 6, 10),  # Gonzaga (scheduled)
        ]

        for game_idx, predicted_winner_idx, points in picks_data:
            game = games[game_idx]
            predicted_winner = teams[predicted_winner_idx]

            pick = Pick(
                bracket_id=bracket.id,
                game_id=game.id,
                predicted_winner_id=predicted_winner.id,
                points_value=points,
                points_earned=0,
            )

            # Calculate if pick is correct (for completed games)
            if game.status == "completed":
                actual_winner_id = (
                    game.home_team_id if game.home_score > game.away_score else game.away_team_id
                )
                if predicted_winner.id == actual_winner_id:
                    pick.is_correct = True
                    pick.points_earned = points
                else:
                    pick.is_correct = False
                    pick.points_earned = 0

            session.add(pick)

        session.commit()
        print(f"✓ Created {len(picks_data)} picks")

        # Update bracket totals
        from app.services.scoring_engine import ScoringEngine

        engine_service = ScoringEngine(session)
        scores = engine_service.calculate_bracket_score(bracket.id)
        print(f"✓ Calculated bracket scores: {scores}")

        print("\n✅ Database seeded successfully!")
        print(f"\nSummary:")
        print(f"  - User: {user.email}")
        print(f"  - Tournament: {tournament.name}")
        print(f"  - Teams: {len(teams)}")
        print(f"  - Games: {len(games)}")
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
