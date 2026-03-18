"""Unit tests for notification scheduler."""
import pytest
from unittest.mock import MagicMock
from app.services.notification_scheduler import NotificationScheduler


def test_scheduled_game_needs_notification():
    """Test that scheduled games with no notification get game_start notification."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    # Create mock game
    game = MagicMock()
    game.id = 1
    game.status = "scheduled"
    game.last_notified_event = None
    game.home_team_name = "Duke"
    game.away_team_name = "UNC"
    game.home_team_seed = 1
    game.away_team_seed = 2

    # Mock database query
    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "game_start"
    assert "Game starting" in notifications[0]["message"]


def test_in_progress_game_needs_halftime_notification():
    """Test that in-progress games get halftime notification."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    game = MagicMock()
    game.id = 1
    game.status = "in_progress"
    game.last_notified_event = "game_start"  # Already sent start notification
    game.home_team_name = "Duke"
    game.away_team_name = "UNC"
    game.home_score = 45
    game.away_score = 42
    game.home_team_seed = 1
    game.away_team_seed = 2

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "halftime"
    assert "Halftime" in notifications[0]["message"]


def test_completed_game_with_upset_needs_notification():
    """Test that completed games with upset get upset notification."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    # Lower seed (16) beats higher seed (1) - UPSET!
    game = MagicMock()
    game.id = 1
    game.status = "completed"
    game.last_notified_event = "in_progress"
    game.home_team_name = "Hampton"  # 16 seed
    game.away_team_name = "Duke"  # 1 seed
    game.home_score = 85
    game.away_score = 80
    game.home_team_seed = 16
    game.away_team_seed = 1

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "upset"
    assert "UPSET" in notifications[0]["message"]


def test_completed_game_no_upset_needs_final_notification():
    """Test that completed games without upset get final notification."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    # Higher seed (1) beats lower seed (16) - not an upset
    game = MagicMock()
    game.id = 1
    game.status = "completed"
    game.last_notified_event = "in_progress"
    game.home_team_name = "Duke"  # 1 seed
    game.away_team_name = "Hampton"  # 16 seed
    game.home_score = 90
    game.away_score = 65
    game.home_team_seed = 1
    game.away_team_seed = 16

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "game_final"
    assert "Final" in notifications[0]["message"]


def test_no_notifications_when_already_sent():
    """Test that no notifications returned when already sent for current status."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    # Completed game with final notification already sent
    game = MagicMock()
    game.id = 1
    game.status = "completed"
    game.last_notified_event = "completed"
    game.home_team_name = "Duke"
    game.away_team_name = "UNC"
    game.home_score = 75
    game.away_score = 70
    game.home_team_seed = 1
    game.away_team_seed = 2

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 0


def test_mark_notification_sent():
    """Test marking notification as sent updates game."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    game = MagicMock()
    game.id = 1
    game.status = "completed"
    game.last_notified_event = None

    result = MagicMock()
    result.scalar_one_or_none.return_value = game
    mock_db.execute = MagicMock(return_value=result)
    mock_db.commit = MagicMock()

    scheduler.mark_notification_sent(1, "game_final")

    assert game.last_notified_event == "game_final"
    mock_db.commit.assert_called_once()


def test_upset_detection_away_team_lower_seed():
    """Test upset detection when away team (lower seed) wins."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    # Away team (seed 16) beats home team (seed 1)
    game = MagicMock()
    game.id = 1
    game.status = "completed"
    game.last_notified_event = "in_progress"
    game.home_team_name = "Duke"  # 1 seed
    game.away_team_name = "Hampton"  # 16 seed
    game.home_score = 80
    game.away_score = 85
    game.home_team_seed = 1
    game.away_team_seed = 16

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "upset"


def test_multiple_games_needing_different_notifications():
    """Test handling multiple games with different notification needs."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    # Game 1: Scheduled, needs game_start
    game1 = MagicMock()
    game1.id = 1
    game1.status = "scheduled"
    game1.last_notified_event = None
    game1.home_team_name = "Duke"
    game1.away_team_name = "UNC"
    game1.home_team_seed = 1
    game1.away_team_seed = 2

    # Game 2: In progress, needs halftime
    game2 = MagicMock()
    game2.id = 2
    game2.status = "in_progress"
    game2.last_notified_event = "game_start"
    game2.home_team_name = "Kansas"
    game2.away_team_name = "Texas"
    game2.home_score = 40
    game2.away_score = 38
    game2.home_team_seed = 3
    game2.away_team_seed = 14

    # Game 3: Completed, needs final
    game3 = MagicMock()
    game3.id = 3
    game3.status = "completed"
    game3.last_notified_event = "in_progress"
    game3.home_team_name = "Gonzaga"
    game3.away_team_name = "Stanford"
    game3.home_score = 72
    game3.away_score = 60
    game3.home_team_seed = 1
    game3.away_team_seed = 16

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game1, game2, game3]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 3
    assert notifications[0]["event_type"] == "game_start"
    assert notifications[1]["event_type"] == "halftime"
    assert notifications[2]["event_type"] == "game_final"


def test_in_progress_game_not_notified_twice():
    """Test that in_progress notification doesn't trigger again for same game."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    game = MagicMock()
    game.id = 1
    game.status = "in_progress"
    game.last_notified_event = "in_progress"
    game.home_team_name = "Duke"
    game.away_team_name = "UNC"
    game.home_score = 50
    game.away_score = 48
    game.home_team_seed = 1
    game.away_team_seed = 2

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    assert len(notifications) == 0


def test_mark_notification_sent_nonexistent_game():
    """Test mark_notification_sent with nonexistent game ID."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute = MagicMock(return_value=result)
    mock_db.commit = MagicMock()

    scheduler.mark_notification_sent(999, "game_final")

    # commit should not be called if game doesn't exist
    mock_db.commit.assert_not_called()


def test_upset_with_none_scores():
    """Test upset detection gracefully handles missing scores."""
    mock_db = MagicMock()
    scheduler = NotificationScheduler(mock_db)

    game = MagicMock()
    game.id = 1
    game.status = "completed"
    game.last_notified_event = "in_progress"
    game.home_team_name = "Duke"
    game.away_team_name = "Hampton"
    game.home_score = None
    game.away_score = None
    game.home_team_seed = 1
    game.away_team_seed = 16

    result = MagicMock()
    result.scalars.return_value.all.return_value = [game]
    mock_db.execute = MagicMock(return_value=result)

    notifications = scheduler.get_games_needing_notification()

    # With None scores, should not be considered an upset
    assert len(notifications) == 1
    assert notifications[0]["event_type"] == "game_final"
