"""
Service de decouverte des stations meteo dans le catalogue ODS.

Utilise une LinkedList pour stocker les datasets detectes.
"""

from __future__ import annotations

from meteo_toulouse.config import JSONLike
from meteo_toulouse.data_structures import LinkedList
from meteo_toulouse.models import Station
from meteo_toulouse.utils import norm
from meteo_toulouse.client import ODSClient
from meteo_toulouse.repository import WeatherRepositoryMemory


class StationCatalogSimple:
    """
    Service de decouverte des stations meteo dans le catalogue.

    Utilise une LinkedList pour stocker les datasets detectes.

    Attributes:
        ods: Client HTTP ODS.
        repo: Repository pour stocker les stations.
        _weather: LinkedList des datasets meteo detectes.
    """

    TEMP_TOKENS = {
        "temperature", "temperatures", "temperature", "tair", "temp_c", "tc",
        "temp", "temperature_c",
    }
    HUM_TOKENS = {
        "humidity", "humidite", "humidite", "rh", "hr", "humidite_rel", "hum_rel",
    }
    PRESS_TOKENS = {
        "pression", "pressure", "press_hpa", "pression_hpa", "hpa",
    }
    WIND_TOKENS = {
        "vent", "wind", "rafale", "rafales", "gust", "ff", "ff10", "dd",
        "direction_vent", "vitesse_vent", "vent_ms",
    }
    RAIN_TOKENS = {
        "rain", "pluie", "pluvio", "precipitation", "precipitations", "rr",
        "rr1", "rr24", "rr24h",
    }

    EXCLUDE_DATASET_IDS = {
        "previsions-meteo-france-metropole",
    }

    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory) -> None:
        """
        Initialise le catalogue.

        Args:
            ods: Client HTTP ODS.
            repo: Repository pour stocker les stations.
        """
        self.ods = ods
        self.repo = repo
        self._weather: LinkedList[JSONLike] = LinkedList()

    def _is_weather_like(self, ds: JSONLike) -> bool:
        """Detecte si un dataset est une station meteo."""
        dsid = ds.get("dataset_id")
        if not dsid:
            return False

        if "station-meteo-" not in dsid:
            return False

        if dsid in self.EXCLUDE_DATASET_IDS:
            return False

        fields = ds.get("fields", []) or []
        fields_text = " ".join(
            f"{norm(f.get('name') or '')} {norm(f.get('label') or '')}"
            for f in fields
        )

        buf = []
        for ch in fields_text:
            if ch.isalnum():
                buf.append(ch)
            else:
                buf.append(" ")
        tokens = {tok for tok in "".join(buf).split() if tok}

        groups = 0
        if tokens & self.TEMP_TOKENS:
            groups += 1
        if tokens & self.HUM_TOKENS:
            groups += 1
        if tokens & self.PRESS_TOKENS:
            groups += 1
        if tokens & self.WIND_TOKENS:
            groups += 1
        if tokens & self.RAIN_TOKENS:
            groups += 1

        if groups == 0:
            return False

        has_geo = any((f.get("type") == "geo_point_2d") for f in fields)
        return (groups >= 2) or (groups >= 1 and has_geo)

    def load(self) -> None:
        """Charge le catalogue et detecte les stations meteo."""
        print("Chargement du catalogue (stations meteo Toulouse)...")

        for ds in self.ods.catalog_datasets_iter():
            if self._is_weather_like(ds):
                self._weather.append(ds)

        # Creation des stations dans le repository
        for ds in self._weather:
            metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
            title = metas.get("title") or ds.get("dataset_id")
            dsid = ds.get("dataset_id")
            if not dsid:
                continue
            st = Station(id=dsid, name=str(title), dataset_id=str(dsid), meta=metas)
            self.repo.upsert_station(st)

    def datasets(self) -> list[JSONLike]:
        """Retourne la liste des datasets meteo detectes."""
        return self._weather.to_list()
