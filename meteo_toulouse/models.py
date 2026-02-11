"""
Modeles de domaine: Station et WeatherRecord.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from meteo_toulouse.config import JSONLike


@dataclass
class Station:
    """
    Modele representant une station meteo.

    Attributes:
        id: Identifiant unique de la station.
        name: Nom affichable de la station.
        dataset_id: Identifiant du dataset ODS correspondant.
        meta: Metadonnees supplementaires.
    """
    id: str
    name: str
    dataset_id: str
    meta: JSONLike = field(default_factory=dict)


@dataclass
class WeatherRecord:
    """
    Modele representant une observation meteo.

    Attributes:
        station_id: ID de la station source.
        timestamp: Date/heure de l'observation.
        temperature_c: Temperature en degres Celsius.
        humidity_pct: Humidite relative en pourcentage.
        pressure_hpa: Pression atmospherique en hPa.
        wind_speed_ms: Vitesse du vent en m/s.
        wind_dir_deg: Direction du vent en degres.
        rain_mm: Precipitations en mm.
        raw: Donnees brutes originales.
    """
    station_id: str
    timestamp: datetime | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    wind_speed_ms: float | None = None
    wind_dir_deg: float | None = None
    rain_mm: float | None = None
    raw: JSONLike = field(default_factory=dict)
