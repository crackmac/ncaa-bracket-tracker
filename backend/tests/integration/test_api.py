"""Integration tests for API endpoints."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.models import Bracket, Tournament, Team, Game, User
from app.api.deps import get_db


@pytest.fixture
def test_client():
    """Create test client with in-memory database."""
    # Create in-memory database with a static pool to maintain connection
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    # Seed minimal data
    db = TestingSessionLocal()
    user = User(name="Test User", email="test@example.com")
    db.add(user)

    tournament = Tournament(
        year=2026,
        name="Test Tournament",
        start_date=datetime(2026, 3, 17),
        end_date=datetime(2026, 4, 6)
    )
    db.add(tournament)
    db.flush()

    # Add 2 teams
    team1 = Team(tournament_id=tournament.id, name="Duke", seed=1, region="East", espn_id="d1")
    team2 = Team(tournament_id=tournament.id, name="Hampton", seed=16, region="East", espn_id="h16")
    db.add_all([team1, team2])
    db.flush()

    # Add 1 game
    game = Game(
        tournament_id=tournament.id,
        espn_id="g1",
        round="Round 64",
        region="East",
        home_team_id=team1.id,
        away_team_id=team2.id,
        status="scheduled"
    )
    db.add(game)
    db.commit()

    # Override dependency to use test database
    def override_get_db():
        try:
            yield db
        finally:
            pass  # Don't close, keep connection open for test

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Cleanup
    db.close()
    app.dependency_overrides.clear()


def test_create_bracket_with_valid_picks(test_client):
    """Test creating bracket with all required picks."""
    response = test_client.post(
        "/api/v1/brackets",
        json={
            "name": "Test Bracket",
            "bracket_type": "chalk",
            "picks": [
                {"game_id": 1, "predicted_winner_id": 1}
            ]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Bracket"
    assert "id" in data


def test_create_bracket_rejects_missing_picks(test_client):
    """Test creating bracket without all picks fails."""
    response = test_client.post(
        "/api/v1/brackets",
        json={
            "name": "Incomplete Bracket",
            "bracket_type": "chalk",
            "picks": []
        }
    )

    assert response.status_code == 400
    assert "picks" in response.json()["detail"].lower()


def _add_older_tournament_and_second_user():
    """Simulate a database that has kept last year's tournament and has more than one user."""
    db = next(app.dependency_overrides[get_db]())
    older = Tournament(year=2025, name="Last Year", start_date=datetime(2025, 3, 18), end_date=datetime(2025, 4, 7))
    db.add_all([older, User(name="Second User", email="second@example.com")])
    db.commit()
    return db


def test_create_bracket_uses_latest_tournament_when_several_exist(test_client):
    """Bracket creation picks the newest tournament instead of failing on multiple rows."""
    db = _add_older_tournament_and_second_user()

    response = test_client.post(
        "/api/v1/brackets",
        json={
            "name": "Two Seasons",
            "bracket_type": "chalk",
            "picks": [{"game_id": 1, "predicted_winner_id": 1}],
        },
    )

    assert response.status_code == 201, response.json()
    bracket = db.get(Bracket, response.json()["id"])
    assert bracket.tournament.year == 2026
    assert bracket.user.email == "test@example.com"
