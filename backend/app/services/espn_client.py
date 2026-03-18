import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("app.espn_client")


class ESPNTeam(BaseModel):
    """ESPN team data model."""

    id: str
    name: str
    abbreviation: str
    displayName: str


class ESPNCompetitor(BaseModel):
    """ESPN competitor data model."""

    id: str
    team: ESPNTeam
    score: str | None = None
    homeAway: str


class ESPNCompetition(BaseModel):
    """ESPN competition data model."""

    id: str
    date: str
    competitors: list[ESPNCompetitor]
    status: dict[str, Any]


class ESPNEvent(BaseModel):
    """ESPN event data model."""

    id: str
    name: str
    shortName: str
    competitions: list[ESPNCompetition]


class ESPNClient:
    """Client for fetching NCAA tournament data from ESPN API."""

    def __init__(self):
        self.base_url = settings.espn_api_base_url
        self.cache: dict[str, tuple[datetime, Any]] = {}
        self.cache_ttl = settings.espn_cache_ttl

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache:
            return False
        cached_time, _ = self.cache[key]
        age = (datetime.utcnow() - cached_time).total_seconds()
        return age < self.cache_ttl

    def _get_from_cache(self, key: str) -> Any | None:
        """Get data from cache if valid."""
        if self._is_cache_valid(key):
            _, data = self.cache[key]
            return data
        return None

    def _save_to_cache(self, key: str, data: Any) -> None:
        """Save data to cache."""
        self.cache[key] = (datetime.utcnow(), data)

    async def get_tournament_games(self, date: str | None = None) -> list[ESPNEvent]:
        """Fetch tournament games from ESPN API.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            List of game events

        Raises:
            httpx.HTTPError: If API request fails
        """
        cache_key = f"tournament_games_{date or 'today'}"

        # Check cache first
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug(f"Returning cached tournament games for date: {date or 'today'}")
            return cached

        try:
            url = f"{self.base_url}/scoreboard"
            params = {}
            if date:
                params["dates"] = date

            logger.info(f"Fetching games from ESPN API: {url}", extra={"date": date})

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                events = []

                if "events" in data:
                    for event_data in data["events"]:
                        try:
                            event = ESPNEvent(**event_data)
                            events.append(event)
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse event data: {e}",
                                exc_info=True,
                                extra={"event_id": event_data.get("id")},
                            )
                            continue

                logger.info(f"Successfully fetched {len(events)} games from ESPN")

                # Cache results
                self._save_to_cache(cache_key, events)
                return events

        except httpx.HTTPError as e:
            logger.error(f"ESPN API request failed: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching ESPN data: {e}", exc_info=True)
            raise

    async def get_tournament_games_with_retry(
        self, date: str | None = None, max_retries: int = 3
    ) -> list[ESPNEvent]:
        """Fetch games with retry logic.

        Args:
            date: Date in YYYY-MM-DD format
            max_retries: Maximum number of retry attempts

        Returns:
            List of game events
        """
        for attempt in range(max_retries):
            try:
                return await self.get_tournament_games(date)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} after {wait_time}s due to: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} retry attempts failed")
                    raise

    async def get_game_details(self, game_id: str) -> ESPNEvent | None:
        """
        Fetch detailed information for a specific game.

        Args:
            game_id: ESPN game ID.

        Returns:
            ESPN event data or None if not found.
        """
        cache_key = f"game_{game_id}"

        # Check cache first
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug(f"Returning cached game details for game_id: {game_id}")
            return cached

        # Fetch from ESPN
        url = f"{self.base_url}/summary"
        params = {"event": game_id}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"Fetching game details from ESPN API: {url}", extra={"game_id": game_id})
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if "header" in data and "competition" in data["header"]:
                    # Parse event from summary data
                    event_data = {
                        "id": game_id,
                        "name": data.get("header", {}).get("name", ""),
                        "shortName": data.get("header", {}).get("shortName", ""),
                        "competitions": [data["header"]["competition"]],
                    }
                    event = ESPNEvent(**event_data)

                    # Cache result
                    self._save_to_cache(cache_key, event)
                    logger.info(f"Successfully fetched game details for game_id: {game_id}")
                    return event
                else:
                    logger.warning(
                        f"Unexpected response structure for game {game_id}: missing header or competition data"
                    )
                    return None

        except httpx.HTTPError as e:
            logger.error(f"ESPN API request failed for game {game_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching game details for {game_id}: {e}", exc_info=True)
            return None


# Global ESPN client instance
espn_client = ESPNClient()
