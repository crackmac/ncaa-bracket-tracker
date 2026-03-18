from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.sync_service import SyncService
from app.services.espn_client import espn_client
from app.services.scoring_engine import ScoringEngine

router = APIRouter()


class SyncResponse(BaseModel):
    """Sync response model."""

    message: str
    games_updated: int


@router.post("/sync", response_model=SyncResponse)
async def sync_espn_data(db: Session = Depends(get_db)):
    """
    Manually trigger ESPN data sync.
    Fetches latest game data and updates database.
    """
    try:
        sync_service = SyncService(db, espn_client, ScoringEngine)
        result = await sync_service.sync_games()

        return SyncResponse(
            message="Successfully synced ESPN data",
            games_updated=result["games_updated"]
        )
    except Exception as e:
        db.rollback()
        return SyncResponse(
            message=f"Error syncing data: {str(e)}",
            games_updated=0
        )
