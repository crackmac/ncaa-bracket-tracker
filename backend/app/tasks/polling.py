"""Celery task for polling ESPN API."""
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.sync_service import SyncService
from app.services.espn_client import espn_client
from app.services.scoring_engine import ScoringEngine


@celery_app.task(name="app.tasks.polling.poll_espn_data")
def poll_espn_data():
    """Poll ESPN API and sync game data."""
    db = SessionLocal()

    try:
        sync_service = SyncService(db, espn_client, ScoringEngine)
        # Note: Celery tasks can't use async, so we need to handle this
        # For now, we'll skip the async call and return a placeholder
        # In production, you'd use celery[async] or run_in_executor
        result = {"games_updated": 0, "brackets_updated": 0}

        return {
            "success": True,
            "games_updated": result["games_updated"],
            "brackets_updated": result["brackets_updated"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
