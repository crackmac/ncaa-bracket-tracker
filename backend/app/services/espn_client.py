from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel

from app.config import settings


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
        """
        Fetch tournament games from ESPN API.

        Args:
            date: Date in YYYYMMDD format. If None, fetches today's games.

        Returns:
            List of ESPN events (games).
        """
        cache_key = f"tournament_games_{date or 'today'}"

        # Check cache first
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # Build URL
        url = f"{self.base_url}/scoreboard"
        params = {}
        if date:
            params["dates"] = date

        # Fetch from ESPN
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        # Parse events
        events = []
        if "events" in data:
            for event_data in data["events"]:
                try:
                    event = ESPNEvent(**event_data)
                    events.append(event)
                except Exception as e:
                    print(f"Failed to parse event: {e}")
                    continue

        # Cache results
        self._save_to_cache(cache_key, events)
        return events

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
            return cached

        # Fetch from ESPN
        url = f"{self.base_url}/summary"
        params = {"event": game_id}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=10.0)
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
                    return event

            except Exception as e:
                print(f"Failed to fetch game {game_id}: {e}")

        return None


# Global ESPN client instance
espn_client = ESPNClient()
