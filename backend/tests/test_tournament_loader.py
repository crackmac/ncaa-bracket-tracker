import pytest
from pathlib import Path
from datetime import datetime


def test_parse_valid_tournament_yaml():
    """Test parsing a valid tournament YAML file."""
    from scripts.load_tournament import parse_tournament_yaml

    yaml_path = Path("data/tournaments/2026.yaml")
    result = parse_tournament_yaml(yaml_path)

    assert result["tournament"]["year"] == 2026
    assert result["tournament"]["name"] == "NCAA March Madness 2026"
    assert len(result["regions"]) == 4
    assert len(result["matchups"]["round_64"]) == 32


def test_validate_tournament_structure():
    """Test tournament structure validation."""
    from scripts.load_tournament import validate_tournament

    yaml_path = Path("data/tournaments/2026.yaml")
    from scripts.load_tournament import parse_tournament_yaml
    data = parse_tournament_yaml(yaml_path)

    # Should not raise exception
    validate_tournament(data)


def test_validate_rejects_invalid_team_count():
    """Test validation rejects wrong number of teams."""
    from scripts.load_tournament import validate_tournament

    invalid_data = {
        "tournament": {"year": 2026, "name": "Test", "start_date": "2026-03-17", "end_date": "2026-04-06"},
        "regions": [
            {"name": "East", "teams": [{"name": "Duke", "seed": 1, "espn_id": "duke"}]}  # Only 1 team
        ],
        "matchups": {"round_64": []}
    }

    with pytest.raises(ValueError, match="must have exactly 16 teams"):
        validate_tournament(invalid_data)


def test_validate_rejects_invalid_seeds():
    """Test validation rejects invalid seed numbers."""
    from scripts.load_tournament import validate_tournament

    teams = [{"name": f"Team{i}", "seed": i, "espn_id": f"t{i}"} for i in range(1, 17)]
    teams[0]["seed"] = 0  # Invalid seed

    invalid_data = {
        "tournament": {"year": 2026, "name": "Test", "start_date": "2026-03-17", "end_date": "2026-04-06"},
        "regions": [{"name": "East", "teams": teams}],
        "matchups": {"round_64": []}
    }

    with pytest.raises(ValueError, match="Seeds must be 1-16"):
        validate_tournament(invalid_data)
