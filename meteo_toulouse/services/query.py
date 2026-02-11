"""
Service Layer Pattern: Consultation des donnees meteo.
"""

from __future__ import annotations

from meteo_toulouse.models import WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory


class WeatherQueryService:
    """Service Layer Pattern: Consultation des donnees meteo."""

    def __init__(self, repo: WeatherRepositoryMemory) -> None:
        self.repo = repo

    def latest_for_station(self, station_id: str, n: int = 1) -> list[WeatherRecord]:
        """Recupere les N dernieres observations d'une station."""
        return self.repo.latest_records(station_id, n=n)
