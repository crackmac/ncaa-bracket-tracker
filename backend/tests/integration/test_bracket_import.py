"""Integration tests for bracket import endpoint."""
from datetime import datetime
import json
from io import BytesIO

import pytest
import yaml
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

    # Seed test data
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

    # Add teams (use IDs 1 and 2)
    team1 = Team(tournament_id=tournament.id, name="Duke", seed=1, region="East", espn_id="d1")
    team2 = Team(tournament_id=tournament.id, name="Hampton", seed=16, region="East", espn_id="h16")
    db.add_all([team1, team2])
    db.flush()

    # Add game
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


def test_import_bracket_from_yaml(test_client):
    """Test importing a bracket from a valid YAML file."""
    yaml_content = {
        "name": "YAML Bracket",
        "bracket_type": "chalk",
        "picks": [
            {"game_id": 1, "winner": "Duke"}
        ]
    }
    yaml_string = yaml.dump(yaml_content)

    response = test_client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.yaml", BytesIO(yaml_string.encode()), "application/yaml")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "YAML Bracket"
    assert data["bracket_type"] == "chalk"
    assert "id" in data


def test_import_bracket_from_json(test_client):
    """Test importing a bracket from a valid JSON file."""
    json_content = {
        "name": "JSON Bracket",
        "bracket_type": "balanced",
        "picks": [
            {"game_id": 1, "winner": "1"}
        ]
    }
    json_string = json.dumps(json_content)

    response = test_client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.json", BytesIO(json_string.encode()), "application/json")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "JSON Bracket"
    assert data["bracket_type"] == "balanced"
    assert "id" in data


def test_import_rejects_invalid_format(test_client):
    """Test that invalid file format is rejected."""
    invalid_content = "this is not valid yaml or json: {["

    response = test_client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.txt", BytesIO(invalid_content.encode()), "text/plain")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_import_resolves_team_names(test_client):
    """Test that team names (case-insensitive) are resolved to team IDs."""
    yaml_content = {
        "name": "Name Resolution Bracket",
        "bracket_type": "chalk",
        "picks": [
            {"game_id": 1, "winner": "duke"}  # lowercase should match "Duke"
        ]
    }
    yaml_string = yaml.dump(yaml_content)

    response = test_client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.yaml", BytesIO(yaml_string.encode()), "application/yaml")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Name Resolution Bracket"


def test_import_rejects_invalid_team_name(test_client):
    """Test that invalid team names are rejected."""
    yaml_content = {
        "name": "Invalid Team Bracket",
        "bracket_type": "chalk",
        "picks": [
            {"game_id": 1, "winner": "NonExistentTeam"}
        ]
    }
    yaml_string = yaml.dump(yaml_content)

    response = test_client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.yaml", BytesIO(yaml_string.encode()), "application/yaml")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_import_uses_latest_tournament_when_several_exist(test_client):
    """Import picks the newest tournament instead of failing when last year's is still stored."""
    db = next(app.dependency_overrides[get_db]())
    older = Tournament(year=2025, name="Last Year", start_date=datetime(2025, 3, 18), end_date=datetime(2025, 4, 7))
    db.add_all([older, User(name="Second User", email="second@example.com")])
    db.commit()

    yaml_string = yaml.dump({"name": "Two Seasons", "bracket_type": "chalk", "picks": [{"game_id": 1, "winner": "Duke"}]})
    response = test_client.post(
        "/api/v1/brackets/import",
        files={"file": ("bracket.yaml", BytesIO(yaml_string.encode()), "application/yaml")}
    )

    assert response.status_code == 201, response.json()
    bracket = db.get(Bracket, response.json()["id"])
    assert bracket.tournament.year == 2026
