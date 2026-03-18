"""Tests for Celery tasks."""
import pytest
from unittest.mock import patch, MagicMock

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
            mock_sync_class.return_value = mock_sync

            # Execute task
            result = poll_espn_data()

            # Verify success
            assert result["success"] is True
            assert "games_updated" in result
            assert "brackets_updated" in result

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
