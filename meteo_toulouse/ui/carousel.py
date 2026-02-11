"""
Strategy Pattern: Carrousel cyclique des stations.

Utilise une Queue pour gerer le parcours cyclique des stations.
"""

from __future__ import annotations

import time

from meteo_toulouse.config import PRINT_WIDTH
from meteo_toulouse.data_structures import Queue
from meteo_toulouse.models import Station
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.services.forecast import ForecastService


class StationCarouselRenderer:
    """
    Strategy Pattern: Carrousel cyclique des stations.

    Utilise une Queue pour gerer le parcours cyclique des stations.
    """

    def __init__(self, repo: WeatherRepositoryMemory, forecast: ForecastService, delay_seconds: int = 5) -> None:
        self.repo = repo
        self.forecast = forecast
        self.delay_seconds = delay_seconds
        self._queue: Queue[Station] = Queue()

    def _load_stations_to_queue(self) -> None:
        """Charge les stations dans la queue."""
        for st in self.repo.list_stations():
            self._queue.enqueue(st)

    def _format_record_line(self, st: Station) -> str:
        """Formate l'affichage d'une station."""
        latest = self.repo.latest_records(st.id, n=1)
        if not latest:
            return f"[{st.dataset_id}] {st.name}\n  Aucune observation recente disponible."
        r = latest[0]
        ts = r.timestamp.isoformat(sep=" ", timespec="seconds") if r.timestamp else "-"
        t = f"{r.temperature_c:.1f}C" if r.temperature_c is not None else "?"
        hum = f"{r.humidity_pct:.0f}%" if r.humidity_pct is not None else "?"
        ws = f"{r.wind_speed_ms:.1f} m/s" if r.wind_speed_ms is not None else "?"
        rr = f"{r.rain_mm:.1f} mm" if r.rain_mm is not None else "0"
        return (
            f"[{st.dataset_id}] {st.name}\n"
            f"  Derniere obs: {ts}\n"
            f"  T={t}  H={hum}  Vent={ws}  Pluie={rr}"
        )

    def _format_forecast_line(self, st: Station) -> str:
        """Formate la prevision d'une station."""
        yhat = self.forecast.forecast_station_temp(st.id)
        if yhat is None:
            return "  Prevision: indisponible (pas assez de donnees)"
        return f"  Prevision: temp ~ {yhat:.2f}C"

    def run(self) -> None:
        """Lance le carrousel cyclique."""
        self._load_stations_to_queue()

        if self._queue.is_empty():
            print("\nAucune station meteo detectee, rien a afficher.")
            return

        print("\n=== Carrousel des stations (Ctrl+C pour arreter) ===\n")

        try:
            while True:
                st = self._queue.peek()
                if st is None:
                    break

                print("=" * PRINT_WIDTH)
                print(self._format_record_line(st))
                print(self._format_forecast_line(st))
                print(f"\n-> Station suivante dans {self.delay_seconds} secondes...")

                time.sleep(self.delay_seconds)
                self._queue.rotate()

        except KeyboardInterrupt:
            print("\n\nArret du carrousel.")
