"""
Service Layer Pattern: Previsions meteo (jouet).

Calcule une prevision simple basee sur la moyenne des dernieres observations.
"""

from __future__ import annotations

from meteo_toulouse.repository import WeatherRepositoryMemory


class ForecastService:
    """
    Service Layer Pattern: Previsions meteo (jouet).

    Calcule une prevision simple basee sur la moyenne des dernieres observations.
    """

    def __init__(self, repo: WeatherRepositoryMemory) -> None:
        self.repo = repo

    def forecast_station_temp(self, station_id: str, last_n: int = 3) -> float | None:
        """
        Calcule une prevision de temperature.

        Args:
            station_id: ID de la station.
            last_n: Nombre d'observations a moyenner.

        Returns:
            Temperature prevue ou None si pas assez de donnees.
        """
        rows = self.repo.latest_records(station_id, n=last_n)
        temps = [r.temperature_c for r in rows if r.temperature_c is not None]
        if not temps:
            return None
        return sum(temps) / len(temps)
