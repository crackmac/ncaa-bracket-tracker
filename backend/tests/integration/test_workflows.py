"""Integration tests for end-to-end workflows."""
from datetime import datetime
from io import BytesIO

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.models import Tournament, Team, Game, User, Bracket, Pick
from app.api.deps import get_db
from app.services.scoring_engine import ScoringEngine


@pytest.fixture
def test_client():
    """Create test client with in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    db = TestingSessionLocal()

    user = User(name="Test User", email="test@example.com")
    db.add(user)

    tournament = Tournament(
        year=2026,
        name="Test Tournament",
        start_date=datetime(2026, 3, 17),
        end_date=datetime(2026, 4, 6),
    )
    db.add(tournament)
    db.flush()

    team1 = Team(tournament_id=tournament.id, name="Duke", seed=1, region="East", espn_id="duke")
    team2 = Team(tournament_id=tournament.id, name="Hampton", seed=16, region="East", espn_id="hampton")
    db.add_all([team1, team2])
    db.flush()

    game = Game(
        tournament_id=tournament.id,
        espn_id="game1",
        round="Round 64",
        region="East",
        home_team_id=team1.id,
        away_team_id=team2.id,
        status="scheduled",
    )
    db.add(game)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client, db

    db.close()
    app.dependency_overrides.clear()


def test_full_bracket_workflow(test_client):
    """Test complete workflow: create bracket -> update game -> verify score."""
    client, db = test_client

    # Step 1: Create bracket with picks
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "My Bracket",
            "bracket_type": "chalk",
            "picks": [{"game_id": 1, "predicted_winner_id": 1}],
        },
    )

    assert response.status_code == 201
    bracket_data = response.json()
    bracket_id = bracket_data["id"]

    # Step 2: Verify bracket created
    bracket = db.query(Bracket).filter(Bracket.id == bracket_id).first()
    assert bracket is not None
    assert bracket.name == "My Bracket"
    assert bracket.total_points == 0

    picks = db.query(Pick).filter(Pick.bracket_id == bracket_id).all()
    assert len(picks) == 1
    assert picks[0].is_correct is None

    # Step 3: Simulate game completion (Duke wins)
    game = db.query(Game).filter(Game.id == 1).first()
    game.status = "completed"
    game.home_score = 85
    game.away_score = 70
    db.commit()

    # Step 4: Recalculate scores
    scoring_engine = ScoringEngine(db)
    result = scoring_engine.calculate_bracket_score(bracket_id)

    # Step 5: Verify score updated
    assert result["total_points"] == 10
    assert result["correct_picks"] == 1

    # Verify bracket updated
    bracket = db.query(Bracket).filter(Bracket.id == bracket_id).first()
    assert bracket.total_points == 10

    # Verify pick marked correct
    pick = db.query(Pick).filter(Pick.bracket_id == bracket_id).first()
    assert pick.is_correct is True
    assert pick.points_earned == 10


def test_incorrect_pick_workflow(test_client):
    """Test workflow when user picks wrong team."""
    client, db = test_client

    # Create bracket picking away team (Hampton, seed 16)
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Wrong Pick",
            "bracket_type": "chaos",
            "picks": [{"game_id": 1, "predicted_winner_id": 2}],
        },
    )

    assert response.status_code == 201
    bracket_id = response.json()["id"]

    # Complete game with home team (Duke) winning
    game = db.query(Game).filter(Game.id == 1).first()
    game.status = "completed"
    game.home_score = 90
    game.away_score = 65
    db.commit()

    # Recalculate - should be 0 points
    result = ScoringEngine(db).calculate_bracket_score(bracket_id)

    assert result["total_points"] == 0
    assert result["correct_picks"] == 0

    # Verify pick marked incorrect
    pick = db.query(Pick).filter(Pick.bracket_id == bracket_id).first()
    assert pick.is_correct is False
    assert pick.points_earned == 0


def test_bracket_import_workflow(test_client):
    """Test importing bracket from file and verifying creation."""
    client, db = test_client

    yaml_content = {
        "name": "Imported Bracket",
        "bracket_type": "balanced",
        "picks": [{"game_id": 1, "winner": "Duke"}],
    }
    yaml_string = yaml.dump(yaml_content)

    response = client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.yaml", BytesIO(yaml_string.encode()), "application/yaml")},
    )

    assert response.status_code == 201
    bracket_data = response.json()

    # Verify bracket created
    bracket = db.query(Bracket).filter(Bracket.id == bracket_data["id"]).first()
    assert bracket is not None
    assert bracket.name == "Imported Bracket"
    assert bracket.bracket_type == "balanced"

    picks = db.query(Pick).filter(Pick.bracket_id == bracket.id).all()
    assert len(picks) == 1
    assert picks[0].predicted_winner_id == 1


def test_multiple_games_workflow(test_client):
    """Test bracket with multiple games and progressive scoring."""
    client, db = test_client

    # Add more teams and games
    tournament = db.query(Tournament).first()

    team3 = Team(tournament_id=tournament.id, name="Kansas", seed=2, region="West", espn_id="kansas")
    team4 = Team(tournament_id=tournament.id, name="Howard", seed=15, region="West", espn_id="howard")
    db.add_all([team3, team4])
    db.flush()

    game2 = Game(
        tournament_id=tournament.id,
        espn_id="game2",
        round="Round 64",
        region="West",
        home_team_id=team3.id,
        away_team_id=team4.id,
        status="scheduled",
    )
    db.add(game2)
    db.commit()

    # Create bracket with picks for both games
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Multi-Game Bracket",
            "bracket_type": "balanced",
            "picks": [
                {"game_id": 1, "predicted_winner_id": 1},  # Duke (correct)
                {"game_id": 2, "predicted_winner_id": 4},  # Howard (incorrect - Kansas will win)
            ],
        },
    )

    assert response.status_code == 201
    bracket_id = response.json()["id"]

    # Complete game 1: Duke wins
    game1 = db.query(Game).filter(Game.id == 1).first()
    game1.status = "completed"
    game1.home_score = 80
    game1.away_score = 60
    db.commit()

    # Score after game 1
    result = ScoringEngine(db).calculate_bracket_score(bracket_id)
    assert result["total_points"] == 10
    assert result["correct_picks"] == 1

    # Complete game 2: Kansas wins
    game2 = db.query(Game).filter(Game.id == 2).first()
    game2.status = "completed"
    game2.home_score = 75
    game2.away_score = 55
    db.commit()

    # Final score
    result = ScoringEngine(db).calculate_bracket_score(bracket_id)
    assert result["total_points"] == 10
    assert result["correct_picks"] == 1


def test_upset_detection_workflow(test_client):
    """Test that upset wins are correctly identified."""
    client, db = test_client

    # Create bracket picking favorite (Duke, seed 1)
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Upset Test",
            "bracket_type": "chalk",
            "picks": [{"game_id": 1, "predicted_winner_id": 1}],
        },
    )

    bracket_id = response.json()["id"]

    # Simulate upset: Hampton (16 seed) beats Duke (1 seed)
    game = db.query(Game).filter(Game.id == 1).first()
    game.status = "completed"
    game.home_score = 70
    game.away_score = 75
    db.commit()

    # Score calculation
    scoring_engine = ScoringEngine(db)
    result = scoring_engine.calculate_bracket_score(bracket_id)

    # Upset should be detected
    game = db.query(Game).filter(Game.id == 1).first()
    assert game.is_upset is True

    # Pick should be marked incorrect
    pick = db.query(Pick).filter(Pick.bracket_id == bracket_id).first()
    assert pick.is_correct is False


def test_bracket_retrieval_workflow(test_client):
    """Test retrieving bracket details and score after various game updates."""
    client, db = test_client

    # Create bracket
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Retrieval Test",
            "bracket_type": "chalk",
            "picks": [{"game_id": 1, "predicted_winner_id": 1}],
        },
    )

    bracket_id = response.json()["id"]

    # Before game completion: get bracket
    response = client.get(f"/api/v1/brackets/{bracket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 0
    assert data["correct_picks"] == 0
    assert len(data["picks"]) == 1

    # After game completion: update and retrieve
    game = db.query(Game).filter(Game.id == 1).first()
    game.status = "completed"
    game.home_score = 85
    game.away_score = 70
    db.commit()

    ScoringEngine(db).calculate_bracket_score(bracket_id)

    response = client.get(f"/api/v1/brackets/{bracket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 10
    assert data["correct_picks"] == 1


def test_full_workflow_with_sweet_16(test_client):
    """Test workflow with higher-value round (Sweet 16)."""
    client, db = test_client

    # Add more teams and games to satisfy the validator
    tournament = db.query(Tournament).first()
    team3 = Team(tournament_id=tournament.id, name="Kansas", seed=2, region="West", espn_id="kansas")
    team4 = Team(tournament_id=tournament.id, name="Michigan", seed=3, region="West", espn_id="michigan")
    team5 = Team(tournament_id=tournament.id, name="Auburn", seed=4, region="South", espn_id="auburn")
    team6 = Team(tournament_id=tournament.id, name="Clemson", seed=5, region="South", espn_id="clemson")
    db.add_all([team3, team4, team5, team6])
    db.flush()

    # Add a second Round 64 game to reach 2 total games
    game2 = Game(
        tournament_id=tournament.id,
        espn_id="game2",
        round="Round 64",
        region="West",
        home_team_id=team3.id,
        away_team_id=team4.id,
        status="scheduled",
    )
    db.add(game2)
    db.flush()

    # Add Sweet 16 game
    game_sweet16 = Game(
        tournament_id=tournament.id,
        espn_id="game_s16",
        round="Sweet 16",
        region="South",
        home_team_id=team5.id,
        away_team_id=team6.id,
        status="scheduled",
    )
    db.add(game_sweet16)
    db.commit()

    # Create bracket with 3 picks (must match all 3 games)
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Sweet 16 Test",
            "bracket_type": "balanced",
            "picks": [
                {"game_id": 1, "predicted_winner_id": 1},
                {"game_id": 2, "predicted_winner_id": 3},
                {"game_id": 3, "predicted_winner_id": 5},
            ],
        },
    )

    assert response.status_code == 201
    bracket_id = response.json()["id"]

    # Complete only the Sweet 16 game (game 3)
    game = db.query(Game).filter(Game.espn_id == "game_s16").first()
    game.status = "completed"
    game.home_score = 78
    game.away_score = 72
    db.commit()

    # Calculate score - Sweet 16 = 40 points
    result = ScoringEngine(db).calculate_bracket_score(bracket_id)
    assert result["total_points"] == 40
    assert result["correct_picks"] == 1


def test_bracket_health_calculation_workflow(test_client):
    """Test bracket health metrics calculation."""
    client, db = test_client

    # Create bracket
    response = client.post(
        "/api/v1/brackets",
        json={
            "name": "Health Test",
            "bracket_type": "chalk",
            "picks": [{"game_id": 1, "predicted_winner_id": 1}],
        },
    )

    bracket_id = response.json()["id"]

    scoring_engine = ScoringEngine(db)

    # Before game completion
    health = scoring_engine.get_bracket_health(bracket_id)
    assert health["current_points"] == 0
    assert health["total_picks"] == 1

    # After correct pick
    game = db.query(Game).filter(Game.id == 1).first()
    game.status = "completed"
    game.home_score = 80
    game.away_score = 60
    db.commit()

    health = scoring_engine.get_bracket_health(bracket_id)
    assert health["current_points"] == 10
    assert health["correct_picks"] == 1
    assert health["accuracy"] == 100.0
