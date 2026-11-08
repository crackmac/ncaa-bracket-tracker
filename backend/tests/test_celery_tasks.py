"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.tasks.polling import poll_espn_data


def test_poll_espn_data_success():
    """Test successful ESPN data polling."""
    # Mock database session
    with patch('app.tasks.polling.SessionLocal') as mock_session_class:
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # Mock SyncService
        with patch('app.tasks.polling.SyncService') as mock_sync_class:
            mock_sync = MagicMock()
            mock_sync.sync_games = AsyncMock(return_value={"games_updated": 3, "brackets_updated": 2})
            mock_sync_class.return_value = mock_sync

            # Execute task
            result = poll_espn_data()

            # Verify the sync actually ran and its counts are reported
            mock_sync.sync_games.assert_awaited_once()
            assert result == {"success": True, "games_updated": 3, "brackets_updated": 2}

            # Verify session closed
            mock_db.close.assert_called_once()


def test_poll_espn_data_handles_errors():
    """Test error handling in polling task."""
    with patch('app.tasks.polling.SessionLocal') as mock_session_class:
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        # Make SyncService raise exception
        with patch('app.tasks.polling.SyncService', side_effect=Exception("ESPN API error")):
            result = poll_espn_data()

            # Verify error handling
            assert result["success"] is False
            assert "error" in result
            assert "ESPN API error" in result["error"]

            # Verify session closed even on error
            mock_db.close.assert_called_once()


def test_poll_espn_data_reports_sync_failure():
    """Test that a failure inside the ESPN sync is reported, not hidden."""
    with patch('app.tasks.polling.SessionLocal') as mock_session_class:
        mock_db = MagicMock()
        mock_session_class.return_value = mock_db

        with patch('app.tasks.polling.SyncService') as mock_sync_class:
            mock_sync = MagicMock()
            mock_sync.sync_games = AsyncMock(side_effect=Exception("ESPN timeout"))
            mock_sync_class.return_value = mock_sync

            result = poll_espn_data()

            mock_sync.sync_games.assert_awaited_once()
            assert result["success"] is False
            assert "ESPN timeout" in result["error"]
            mock_db.close.assert_called_once()
