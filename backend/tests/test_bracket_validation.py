"""Tests for bracket validation logic."""
import pytest
from app.services.bracket_validator import BracketValidator, ValidationError


def test_validate_all_games_have_picks():
    """Test validation requires picks for all 63 games."""
    validator = BracketValidator()

    # Only 62 picks (missing one)
    picks = [{"game_id": f"game_{i}", "predicted_winner_id": 1} for i in range(62)]

    with pytest.raises(ValidationError, match="Must have exactly 63 picks"):
        validator.validate_picks(picks, total_games=63)


def test_validate_no_duplicate_game_picks():
    """Test validation rejects duplicate picks for same game."""
    validator = BracketValidator()

    picks = [
        {"game_id": "game_1", "predicted_winner_id": 1},
        {"game_id": "game_1", "predicted_winner_id": 2},  # Duplicate
    ] + [{"game_id": f"game_{i}", "predicted_winner_id": 1} for i in range(2, 63)]

    with pytest.raises(ValidationError, match="Duplicate picks for game"):
        validator.validate_picks(picks, total_games=63)


def test_resolve_team_by_id():
    """Test resolving team by numeric ID."""
    from app.db.models import Team

    validator = BracketValidator()
    mock_teams = {
        1: Team(id=1, tournament_id=1, name="Duke", seed=1, region="East", espn_id="duke")
    }

    result = validator.resolve_team("1", mock_teams)
    assert result == 1


def test_resolve_team_by_name_case_insensitive():
    """Test resolving team by name (case-insensitive)."""
    from app.db.models import Team

    validator = BracketValidator()
    mock_teams = {
        1: Team(id=1, tournament_id=1, name="Duke", seed=1, region="East", espn_id="duke")
    }
    mock_teams_by_name = {"duke": [1]}

    result = validator.resolve_team_by_name("DUKE", mock_teams_by_name)
    assert result == 1


def test_resolve_team_ambiguous_name():
    """Test ambiguous team name raises error."""
    validator = BracketValidator()
    mock_teams_by_name = {"duke": [1, 2]}  # Multiple teams named "Duke"

    with pytest.raises(ValidationError, match="Ambiguous team name"):
        validator.resolve_team_by_name("Duke", mock_teams_by_name)


def test_resolve_team_not_found():
    """Test unknown team name raises error."""
    validator = BracketValidator()
    mock_teams_by_name = {}

    with pytest.raises(ValidationError, match="not found in tournament"):
        validator.resolve_team_by_name("Unknown Team", mock_teams_by_name)
