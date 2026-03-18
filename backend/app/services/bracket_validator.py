"""Bracket validation logic."""
from typing import Any


class ValidationError(Exception):
    """Bracket validation error."""
    pass


class BracketValidator:
    """Validates bracket picks and resolves team references."""

    def validate_picks(self, picks: list[dict[str, Any]], total_games: int) -> None:
        """Validate bracket picks structure.

        Args:
            picks: List of pick dictionaries
            total_games: Expected number of games

        Raises:
            ValidationError: If validation fails
        """
        if len(picks) != total_games:
            raise ValidationError(f"Must have exactly {total_games} picks, got {len(picks)}")

        # Check for duplicate game_ids
        game_ids = [p["game_id"] for p in picks]
        if len(game_ids) != len(set(game_ids)):
            duplicates = [gid for gid in game_ids if game_ids.count(gid) > 1]
            raise ValidationError(f"Duplicate picks for game: {duplicates[0]}")

    def resolve_team(self, winner: str | int, teams_by_id: dict[int, Any]) -> int:
        """Resolve team reference to team ID.

        Args:
            winner: Team ID (int) or name (str)
            teams_by_id: Dictionary of team ID -> Team object

        Returns:
            Team ID

        Raises:
            ValidationError: If team cannot be resolved
        """
        # If numeric, treat as ID
        if isinstance(winner, int) or (isinstance(winner, str) and winner.isdigit()):
            team_id = int(winner)
            if team_id not in teams_by_id:
                raise ValidationError(f"Team ID {team_id} not found")
            return team_id

        # Otherwise, resolve by name
        return self.resolve_team_by_name(winner, self._build_name_map(teams_by_id))

    def resolve_team_by_name(self, name: str, teams_by_name: dict[str, list[int]]) -> int:
        """Resolve team by name (case-insensitive).

        Args:
            name: Team name
            teams_by_name: Dictionary of lowercase name -> list of team IDs

        Returns:
            Team ID

        Raises:
            ValidationError: If name is ambiguous or not found
        """
        name_lower = name.lower()

        if name_lower not in teams_by_name:
            raise ValidationError(f"Team '{name}' not found in tournament")

        team_ids = teams_by_name[name_lower]
        if len(team_ids) > 1:
            raise ValidationError(f"Ambiguous team name '{name}' - use team ID instead")

        return team_ids[0]

    def _build_name_map(self, teams_by_id: dict[int, Any]) -> dict[str, list[int]]:
        """Build name -> team IDs mapping."""
        name_map: dict[str, list[int]] = {}
        for team_id, team in teams_by_id.items():
            name_lower = team.name.lower()
            if name_lower not in name_map:
                name_map[name_lower] = []
            name_map[name_lower].append(team_id)
        return name_map
