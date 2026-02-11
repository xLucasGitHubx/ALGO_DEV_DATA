"""Services metier: catalogue, ingestion, requetes, previsions."""

from meteo_toulouse.services.catalog import StationCatalogSimple
from meteo_toulouse.services.ingestion import WeatherIngestionService
from meteo_toulouse.services.query import WeatherQueryService
from meteo_toulouse.services.forecast import ForecastService

__all__ = [
    "StationCatalogSimple",
    "WeatherIngestionService",
    "WeatherQueryService",
    "ForecastService",
]
