"""
Service Layer Pattern: Ingestion des donnees meteo.

Orchestre le chargement des donnees depuis l'API vers le repository.
"""

from __future__ import annotations

import requests

from meteo_toulouse.utils import norm
from meteo_toulouse.models import Station
from meteo_toulouse.client import ODSClient
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.cleaner import BasicCleaner


class WeatherIngestionService:
    """
    Service Layer Pattern: Ingestion des donnees meteo.

    Orchestre le chargement des donnees depuis l'API vers le repository.
    """

    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory, cleaner: BasicCleaner) -> None:
        self.ods = ods
        self.repo = repo
        self.cleaner = cleaner

    def _find_first_date_field(self, dataset_id: str) -> str | None:
        """Detecte le champ date principal d'un dataset."""
        info = self.ods.dataset_info(dataset_id)
        fields = (info.get("fields") or [])
        preferred = ["date_observation", "date_mesure", "date", "datetime", "timestamp", "time", "heure"]
        by_type = [f.get("name") for f in fields if f.get("type") in ("date", "datetime")]
        for p in preferred:
            if any(norm(f.get("name") or "") == norm(p) for f in fields):
                return p
        return by_type[0] if by_type else None

    def ingest_latest(self, station: Station, max_rows: int = 5) -> int:
        """Ingere les N dernieres observations d'une station."""
        dataset_id = station.dataset_id
        if not dataset_id:
            return 0

        order_field = None
        try:
            order_field = self._find_first_date_field(dataset_id)
        except requests.HTTPError:
            order_field = None

        order_by = f"{order_field} desc" if order_field else None
        count = 0
        try:
            for row in self.ods.iter_records(dataset_id=dataset_id, order_by=order_by, max_rows=max_rows):
                rec = self.cleaner.clean(row, station_id=station.id)
                self.repo.add_record(station.id, rec)
                count += 1
        except requests.HTTPError as e:
            print(f"Echec lecture records ({dataset_id}) : {e}")
        return count

    def ingest_all_latest(self, max_rows_per_station: int = 3, max_stations: int | None = None) -> int:
        """Ingere les observations pour toutes les stations."""
        stations = self.repo.list_stations()
        if max_stations is not None:
            stations = stations[:max_stations]

        total = 0
        for st in stations:
            n = self.ingest_latest(st, max_rows=max_rows_per_station)
            total += n
        return total
