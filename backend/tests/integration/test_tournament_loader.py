"""Integration tests for tournament loader."""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Tournament, Team, Game
from scripts.load_tournament import load_tournament

# Get absolute path to tournament data
TOURNAMENT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "tournaments"


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_load_tournament_creates_all_entities(test_db):
    """Test loading tournament creates all teams and games."""
    yaml_path = TOURNAMENT_DATA_DIR / "2026.yaml"

    tournament_id, teams, games = load_tournament(yaml_path, test_db)

    assert tournament_id > 0
    assert teams == 64
    assert games == 32

    # Verify in database
    assert test_db.query(Tournament).count() == 1
    assert test_db.query(Team).count() == 64
    assert test_db.query(Game).count() == 32


def test_load_tournament_is_idempotent(test_db):
    """Test loading same tournament twice doesn't create duplicates."""
    yaml_path = TOURNAMENT_DATA_DIR / "2026.yaml"

    # Load once
    tournament_id1, teams1, games1 = load_tournament(yaml_path, test_db)

    # Load again
    tournament_id2, teams2, games2 = load_tournament(yaml_path, test_db)

    assert tournament_id1 == tournament_id2
    assert teams2 == 0  # No new teams
    assert games2 == 0  # No new games

    # Still only one tournament
    assert test_db.query(Tournament).count() == 1


def test_load_tournament_teams_have_correct_regions(test_db):
    """Test loaded teams have correct region assignments."""
    yaml_path = TOURNAMENT_DATA_DIR / "2026.yaml"
    load_tournament(yaml_path, test_db)

    regions = ["East", "West", "South", "Midwest"]
    for region in regions:
        teams_in_region = test_db.query(Team).filter(Team.region == region).all()
        assert len(teams_in_region) == 16

        # Check seeds 1-16 all present
        seeds = sorted([t.seed for t in teams_in_region])
        assert seeds == list(range(1, 17))


def test_load_tournament_creates_correct_matchups(test_db):
    """Test Round 64 games have correct seed matchups."""
    yaml_path = TOURNAMENT_DATA_DIR / "2026.yaml"
    load_tournament(yaml_path, test_db)

    games = test_db.query(Game).filter(Game.round == "Round 64").all()
    assert len(games) == 32

    # Check typical matchups (1v16, 8v9, etc.)
    for game in games:
        home_team = test_db.get(Team, game.home_team_id)
        away_team = test_db.get(Team, game.away_team_id)

        # Verify teams are from same region
        assert home_team.region == away_team.region == game.region

        # Verify seed sum is 17 (1+16, 2+15, 3+14, etc.)
        assert home_team.seed + away_team.seed == 17
