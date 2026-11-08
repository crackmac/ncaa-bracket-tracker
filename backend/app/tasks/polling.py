"""Celery task for polling ESPN API."""
import asyncio
import logging
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.sync_service import SyncService
from app.services.espn_client import espn_client
from app.services.scoring_engine import ScoringEngine

logger = logging.getLogger("app.tasks.polling")


@celery_app.task(name="app.tasks.polling.poll_espn_data")
def poll_espn_data():
    """Poll ESPN API and sync game data."""
    logger.info("Polling task started")
    db = SessionLocal()

    try:
        sync_service = SyncService(db, espn_client, ScoringEngine)
        # Celery workers run tasks synchronously, so drive the async sync to completion here
        result = asyncio.run(sync_service.sync_games())

        logger.info(f"Polling complete: {result['games_updated']} games, {result['brackets_updated']} brackets")
        return {
            "success": True,
            "games_updated": result["games_updated"],
            "brackets_updated": result["brackets_updated"]
        }
    except Exception as e:
        logger.error(f"Polling failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
