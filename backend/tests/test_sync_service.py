"""Tests for SyncService using TDD approach."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, call
from sqlalchemy.orm import Session

from app.services.sync_service import SyncService
from app.services.espn_client import ESPNEvent, ESPNCompetition, ESPNCompetitor, ESPNTeam
from app.db.models import Game, Bracket
from app.services.scoring_engine import ScoringEngine


@pytest.fixture
def mock_db() -> Mock:
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_espn_client():
    """Create a mock ESPN client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_scoring_engine_class():
    """Create a mock ScoringEngine class."""
    return Mock(spec=ScoringEngine)


@pytest.fixture
def sync_service(mock_db, mock_espn_client, mock_scoring_engine_class):
    """Create a SyncService instance with mocked dependencies."""
    return SyncService(mock_db, mock_espn_client, mock_scoring_engine_class)


def _create_mock_game(espn_id: str, home_score: int | None = None, away_score: int | None = None, status: str = "scheduled") -> Game:
    """Helper to create a mock Game object."""
    game = Mock(spec=Game)
    game.espn_id = espn_id
    game.home_score = home_score
    game.away_score = away_score
    game.status = status
    return game


def _create_espn_event(event_id: str, home_score: str | None = None, away_score: str | None = None, status_type: str = "STATUS_SCHEDULED") -> ESPNEvent:
    """Helper to create an ESPNEvent for testing."""
    home_competitor = ESPNCompetitor(
        id="home_team",
        team=ESPNTeam(id="home", name="Team A", abbreviation="TA", displayName="Team A"),
        score=home_score,
        homeAway="home"
    )
    away_competitor = ESPNCompetitor(
        id="away_team",
        team=ESPNTeam(id="away", name="Team B", abbreviation="TB", displayName="Team B"),
        score=away_score,
        homeAway="away"
    )

    competition = ESPNCompetition(
        id="comp_1",
        date="2024-03-15",
        competitors=[home_competitor, away_competitor],
        status={"type": {"name": status_type}}
    )

    event = ESPNEvent(
        id=event_id,
        name="Test Game",
        shortName="TG",
        competitions=[competition]
    )

    return event


@pytest.mark.asyncio
async def test_sync_updates_game_scores(sync_service, mock_db, mock_espn_client):
    """Test that sync updates game scores from ESPN data."""
    # Arrange
    game_id = "game_123"
    mock_game = _create_mock_game(game_id, home_score=70, away_score=65)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_game

    espn_event = _create_espn_event(game_id, home_score="70", away_score="65")
    mock_espn_client.get_tournament_games.return_value = [espn_event]

    mock_db.query.return_value.all.return_value = []  # No brackets to update

    # Act
    result = await sync_service.sync_games()

    # Assert
    assert result["games_updated"] == 1
    assert mock_game.home_score == 70
    assert mock_game.away_score == 65
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_sync_updates_game_status(sync_service, mock_db, mock_espn_client):
    """Test that sync updates game status to 'completed' when STATUS_FINAL."""
    # Arrange
    game_id = "game_456"
    mock_game = _create_mock_game(game_id, status="in_progress")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_game

    espn_event = _create_espn_event(game_id, home_score="75", away_score="70", status_type="STATUS_FINAL")
    mock_espn_client.get_tournament_games.return_value = [espn_event]

    mock_db.query.return_value.all.return_value = []  # No brackets

    # Act
    result = await sync_service.sync_games()

    # Assert
    assert result["games_updated"] == 1
    assert mock_game.status == "completed"


@pytest.mark.asyncio
async def test_sync_handles_in_progress_games(sync_service, mock_db, mock_espn_client):
    """Test that sync handles in-progress games correctly."""
    # Arrange
    game_id = "game_789"
    mock_game = _create_mock_game(game_id, status="scheduled")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_game

    espn_event = _create_espn_event(game_id, home_score="35", away_score="28", status_type="STATUS_IN_PROGRESS")
    mock_espn_client.get_tournament_games.return_value = [espn_event]

    mock_db.query.return_value.all.return_value = []  # No brackets

    # Act
    result = await sync_service.sync_games()

    # Assert
    assert result["games_updated"] == 1
    assert mock_game.status == "in_progress"


@pytest.mark.asyncio
async def test_sync_recalculates_bracket_scores(sync_service, mock_db, mock_espn_client, mock_scoring_engine_class):
    """Test that sync recalculates scores for all brackets after updating games."""
    # Arrange
    game_id = "game_999"
    mock_game = _create_mock_game(game_id, home_score="80", away_score="75")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_game

    espn_event = _create_espn_event(game_id, home_score="80", away_score="75", status_type="STATUS_FINAL")
    mock_espn_client.get_tournament_games.return_value = [espn_event]

    # Mock brackets
    mock_bracket_1 = Mock(spec=Bracket)
    mock_bracket_1.id = 1
    mock_bracket_2 = Mock(spec=Bracket)
    mock_bracket_2.id = 2

    # Setup query to return games for first query, then brackets for second query
    query_mock = mock_db.query.return_value
    filter_mock = query_mock.filter.return_value

    # First call: find game by espn_id
    filter_mock.first.return_value = mock_game
    # Second call: get all brackets
    all_mock = Mock()
    all_mock.return_value = [mock_bracket_1, mock_bracket_2]
    query_mock.all = all_mock

    # Mock ScoringEngine instance
    mock_engine_instance = Mock()
    mock_scoring_engine_class.return_value = mock_engine_instance

    # Act
    result = await sync_service.sync_games()

    # Assert
    assert result["games_updated"] == 1
    assert result["brackets_updated"] == 2
    assert mock_scoring_engine_class.call_count == 2
    assert mock_engine_instance.calculate_bracket_score.call_count == 2


@pytest.mark.asyncio
async def test_sync_handles_espn_errors(sync_service, mock_db, mock_espn_client):
    """Test that sync handles ESPN client errors gracefully."""
    # Arrange
    mock_espn_client.get_tournament_games.side_effect = Exception("ESPN API error")

    # Act & Assert - should raise or return error status
    with pytest.raises(Exception, match="ESPN API error"):
        await sync_service.sync_games()
