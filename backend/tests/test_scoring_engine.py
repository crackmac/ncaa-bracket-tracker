"""Unit tests for scoring engine."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.scoring_engine import ScoringEngine, ROUND_POINTS
from app.db.models import Bracket, Pick, Game, Team


def create_team_mock(team_id, seed):
    """Helper to create a Team mock with proper seed attribute."""
    team = MagicMock(spec=Team)
    team.id = team_id
    team.seed = seed
    return team


def test_round_points_values():
    """Test that ROUND_POINTS has correct values."""
    assert ROUND_POINTS["Round 64"] == 10
    assert ROUND_POINTS["Round 32"] == 20
    assert ROUND_POINTS["Sweet 16"] == 40
    assert ROUND_POINTS["Elite 8"] == 80
    assert ROUND_POINTS["Final Four"] == 160
    assert ROUND_POINTS["Championship"] == 320


def test_get_points_for_round():
    """Test getting points for each round."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    assert engine.get_points_for_round("Round 64") == 10
    assert engine.get_points_for_round("Round 32") == 20
    assert engine.get_points_for_round("Sweet 16") == 40
    assert engine.get_points_for_round("Elite 8") == 80
    assert engine.get_points_for_round("Final Four") == 160
    assert engine.get_points_for_round("Championship") == 320
    assert engine.get_points_for_round("Unknown Round") == 10  # Default


def test_calculate_bracket_score_all_correct():
    """Test scoring with all picks correct."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Create mock bracket
    bracket = MagicMock(spec=Bracket)
    bracket.id = 1
    bracket.total_points = 0
    bracket.possible_points = 0

    # Create teams with proper seed attributes
    team1 = create_team_mock(1, 1)
    team2 = create_team_mock(2, 16)
    team3 = create_team_mock(3, 2)
    team4 = create_team_mock(4, 15)

    # Game 1: Round 64, pick correct (team1 wins)
    game1 = MagicMock(spec=Game)
    game1.id = 1
    game1.round = "Round 64"
    game1.home_team_id = 1
    game1.away_team_id = 2
    game1.home_score = 75
    game1.away_score = 70
    game1.status = "completed"
    game1.is_upset = False

    # Game 2: Round 32, pick correct (team3 wins)
    game2 = MagicMock(spec=Game)
    game2.id = 2
    game2.round = "Round 32"
    game2.home_team_id = 3
    game2.away_team_id = 4
    game2.home_score = 80
    game2.away_score = 75
    game2.status = "completed"
    game2.is_upset = False

    pick1 = MagicMock(spec=Pick)
    pick1.bracket_id = 1
    pick1.game_id = 1
    pick1.predicted_winner_id = 1
    pick1.points_value = 10
    pick1.points_earned = 0
    pick1.is_correct = None
    pick1.game = game1

    pick2 = MagicMock(spec=Pick)
    pick2.bracket_id = 1
    pick2.game_id = 2
    pick2.predicted_winner_id = 3
    pick2.points_value = 20
    pick2.points_earned = 0
    pick2.is_correct = None
    pick2.game = game2

    # Mock the database query chain
    def mock_query_impl(model):
        if model == Bracket:
            query = MagicMock()
            query.filter.return_value = MagicMock(first=lambda: bracket)
            return query
        elif model == Pick:
            query = MagicMock()
            query.filter.return_value = MagicMock(all=lambda: [pick1, pick2])
            return query
        elif model == Team:
            query = MagicMock()
            def filter_impl(condition):
                result = MagicMock()
                # Stub for team lookups - they won't be called since games are already complete
                result.first = lambda: None
                return result
            query.filter.side_effect = filter_impl
            return query
        return MagicMock()

    mock_db.query.side_effect = mock_query_impl
    mock_db.commit = MagicMock()

    # Calculate score
    result = engine.calculate_bracket_score(1)

    # Verify results
    assert result["total_points"] == 30  # 10 + 20
    assert result["correct_picks"] == 2
    assert result["total_picks"] == 2
    assert result["possible_points"] == 30


def test_calculate_bracket_score_with_incorrect():
    """Test scoring with some incorrect picks."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Create mock bracket
    bracket = MagicMock(spec=Bracket)
    bracket.id = 1
    bracket.total_points = 0
    bracket.possible_points = 0

    # Create teams
    team1 = create_team_mock(1, 1)
    team2 = create_team_mock(2, 16)

    # Game: Round 64, pick incorrect (picked team 1, but team 2 won)
    game = MagicMock(spec=Game)
    game.id = 1
    game.round = "Round 64"
    game.home_team_id = 1
    game.away_team_id = 2
    game.home_score = 70
    game.away_score = 75  # Team 2 (away) wins
    game.status = "completed"
    game.is_upset = None

    pick = MagicMock(spec=Pick)
    pick.bracket_id = 1
    pick.game_id = 1
    pick.predicted_winner_id = 1  # Predicted team 1, but team 2 won
    pick.points_value = 10
    pick.points_earned = 0
    pick.is_correct = None
    pick.game = game

    # Mock the database query chain
    def mock_query_impl(model):
        if model == Bracket:
            query = MagicMock()
            query.filter.return_value = MagicMock(first=lambda: bracket)
            return query
        elif model == Pick:
            query = MagicMock()
            query.filter.return_value = MagicMock(all=lambda: [pick])
            return query
        elif model == Team:
            query = MagicMock()
            def filter_impl(condition):
                result = MagicMock()
                if "id == 2" in str(condition):
                    result.first = lambda: team2
                elif "id == 1" in str(condition):
                    result.first = lambda: team1
                else:
                    result.first = lambda: None
                return result
            query.filter.side_effect = filter_impl
            return query
        return MagicMock()

    mock_db.query.side_effect = mock_query_impl
    mock_db.commit = MagicMock()

    result = engine.calculate_bracket_score(1)

    assert result["total_points"] == 0
    assert result["correct_picks"] == 0
    assert result["total_picks"] == 1
    assert result["possible_points"] == 0


def test_calculate_bracket_score_mixed_results():
    """Test scoring with mix of correct, incorrect, and incomplete games."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Create mock bracket
    bracket = MagicMock(spec=Bracket)
    bracket.id = 1
    bracket.total_points = 0
    bracket.possible_points = 0

    # Create teams
    team1 = create_team_mock(1, 1)
    team2 = create_team_mock(2, 16)
    team3 = create_team_mock(3, 2)
    team4 = create_team_mock(4, 15)

    # Game 1: Completed, correct pick (Round 64, 10 pts)
    game1 = MagicMock(spec=Game)
    game1.id = 1
    game1.round = "Round 64"
    game1.home_team_id = 1
    game1.away_team_id = 2
    game1.home_score = 75
    game1.away_score = 70
    game1.status = "completed"
    game1.is_upset = False

    # Game 2: Completed, incorrect pick (Round 32, 20 pts)
    game2 = MagicMock(spec=Game)
    game2.id = 2
    game2.round = "Round 32"
    game2.home_team_id = 3
    game2.away_team_id = 4
    game2.home_score = 70
    game2.away_score = 75
    game2.status = "completed"
    game2.is_upset = None

    # Game 3: Not completed yet (Sweet 16, 40 pts potential)
    game3 = MagicMock(spec=Game)
    game3.id = 3
    game3.round = "Sweet 16"
    game3.home_team_id = 1
    game3.away_team_id = 3
    game3.home_score = None
    game3.away_score = None
    game3.status = "scheduled"
    game3.is_upset = False

    pick1 = MagicMock(spec=Pick)
    pick1.bracket_id = 1
    pick1.game_id = 1
    pick1.predicted_winner_id = 1
    pick1.points_value = 10
    pick1.points_earned = 0
    pick1.is_correct = None
    pick1.game = game1

    pick2 = MagicMock(spec=Pick)
    pick2.bracket_id = 1
    pick2.game_id = 2
    pick2.predicted_winner_id = 3
    pick2.points_value = 20
    pick2.points_earned = 0
    pick2.is_correct = None
    pick2.game = game2

    pick3 = MagicMock(spec=Pick)
    pick3.bracket_id = 1
    pick3.game_id = 3
    pick3.predicted_winner_id = 1
    pick3.points_value = 40
    pick3.points_earned = 0
    pick3.is_correct = None
    pick3.game = game3

    # Mock the database query chain
    def mock_query_impl(model):
        if model == Bracket:
            query = MagicMock()
            query.filter.return_value = MagicMock(first=lambda: bracket)
            return query
        elif model == Pick:
            query = MagicMock()
            query.filter.return_value = MagicMock(all=lambda: [pick1, pick2, pick3])
            return query
        elif model == Team:
            query = MagicMock()
            def filter_impl(condition):
                result = MagicMock()
                if "id == 1" in str(condition):
                    result.first = lambda: team1
                elif "id == 2" in str(condition):
                    result.first = lambda: team2
                elif "id == 3" in str(condition):
                    result.first = lambda: team3
                elif "id == 4" in str(condition):
                    result.first = lambda: team4
                else:
                    result.first = lambda: None
                return result
            query.filter.side_effect = filter_impl
            return query
        return MagicMock()

    mock_db.query.side_effect = mock_query_impl
    mock_db.commit = MagicMock()

    result = engine.calculate_bracket_score(1)

    # 1 correct (10 pts) + 1 incorrect (0 pts) = 10 pts total
    # 1 game not decided yet (40 pts possible)
    assert result["total_points"] == 10
    assert result["correct_picks"] == 1
    assert result["total_picks"] == 3
    assert result["possible_points"] == 50  # 10 (current) + 40 (possible)


def test_calculate_bracket_score_bracket_not_found():
    """Test error when bracket doesn't exist."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Mock database to return None for bracket
    bracket_query = MagicMock()
    bracket_query.filter.return_value = MagicMock(first=lambda: None)

    def mock_query_impl(model):
        if model == Bracket:
            return bracket_query
        return MagicMock()

    mock_db.query.side_effect = mock_query_impl

    with pytest.raises(ValueError, match="Bracket 999 not found"):
        engine.calculate_bracket_score(999)


def test_is_upset_higher_seed_wins():
    """Test upset detection when lower-seeded team wins."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Create mock teams - higher seed number is lower seed
    team_1_seed = create_team_mock(1, 1)
    team_16_seed = create_team_mock(16, 16)

    # Game where 16 seed beats 1 seed
    game = MagicMock(spec=Game)
    game.status = "completed"
    game.home_team_id = 1
    game.away_team_id = 16
    game.home_score = 70
    game.away_score = 75  # 16 seed wins
    game.is_upset = False

    # Mock query to track filter calls
    teams_by_id = {1: team_1_seed, 16: team_16_seed}
    call_count = [0]

    def mock_query_impl(model):
        if model == Team:
            query = MagicMock()
            def filter_impl(condition):
                # Each call to filter with Team.id == X gets the corresponding team
                result = MagicMock()
                # Track which team we're looking for by the order of calls
                # First call gets winner (16), second call gets loser (1)
                if call_count[0] == 0:
                    result.first = lambda: team_16_seed
                    call_count[0] += 1
                else:
                    result.first = lambda: team_1_seed
                return result
            query.filter.side_effect = filter_impl
            return query
        return MagicMock()

    mock_db.query.side_effect = mock_query_impl

    # This is an upset - 16 seed beat 1 seed
    result = engine.is_upset(game)
    assert result is True


def test_is_upset_not_upset():
    """Test upset detection when higher-seeded team wins (not upset)."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Create mock teams
    team_1_seed = create_team_mock(1, 1)
    team_16_seed = create_team_mock(16, 16)

    # Game where 1 seed beats 16 seed (expected result)
    game = MagicMock(spec=Game)
    game.status = "completed"
    game.home_team_id = 1
    game.away_team_id = 16
    game.home_score = 75
    game.away_score = 70  # 1 seed wins
    game.is_upset = False

    # Mock query to return teams
    def mock_query_impl(model):
        if model == Team:
            query = MagicMock()
            def filter_impl(condition):
                result = MagicMock()
                if "id == 1" in str(condition):
                    result.first = lambda: team_1_seed
                elif "id == 16" in str(condition):
                    result.first = lambda: team_16_seed
                else:
                    result.first = lambda: None
                return result
            query.filter.side_effect = filter_impl
            return query
        return MagicMock()

    mock_db.query.side_effect = mock_query_impl

    # This is not an upset - 1 seed beat 16 seed as expected
    result = engine.is_upset(game)
    assert result is False


def test_is_upset_incomplete_game():
    """Test upset detection returns False for incomplete games."""
    mock_db = MagicMock()
    engine = ScoringEngine(mock_db)

    # Game not completed yet
    game = MagicMock(spec=Game)
    game.status = "scheduled"
    game.home_team_id = 1
    game.away_team_id = 16
    game.home_score = None
    game.away_score = None
    game.is_upset = False

    result = engine.is_upset(game)
    assert result is False
