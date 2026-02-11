"""Tests pour le service StationCatalogSimple (avec mocks)."""

from unittest.mock import MagicMock
from meteo_toulouse.services.catalog import StationCatalogSimple
from meteo_toulouse.repository import WeatherRepositoryMemory


def _make_weather_dataset(dsid: str = "01-station-meteo-toulouse-test") -> dict:
    """Cree un dataset meteo-like pour les tests."""
    return {
        "dataset_id": dsid,
        "fields": [
            {"name": "temperature", "label": "Temperature", "type": "double"},
            {"name": "humidity", "label": "Humidite", "type": "double"},
            {"name": "pressure", "label": "Pression", "type": "double"},
            {"name": "wind_speed", "label": "Vitesse vent", "type": "double"},
            {"name": "geo_point", "label": "Position", "type": "geo_point_2d"},
        ],
        "metas": {
            "default": {
                "title": "Station Test",
                "records_count": 1000,
            }
        },
    }


def _make_non_weather_dataset() -> dict:
    return {
        "dataset_id": "population-toulouse",
        "fields": [
            {"name": "population", "label": "Population", "type": "int"},
        ],
        "metas": {"default": {"title": "Population"}},
    }


class TestIsWeatherLike:
    def test_weather_dataset_detected(self):
        ods = MagicMock()
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        ds = _make_weather_dataset()
        assert catalog._is_weather_like(ds) is True

    def test_non_weather_dataset_rejected(self):
        ods = MagicMock()
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        ds = _make_non_weather_dataset()
        assert catalog._is_weather_like(ds) is False

    def test_no_dataset_id_rejected(self):
        ods = MagicMock()
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        assert catalog._is_weather_like({}) is False

    def test_excluded_dataset_rejected(self):
        ods = MagicMock()
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        ds = _make_weather_dataset("previsions-meteo-france-metropole")
        # Pas "station-meteo-" dans l'ID, donc rejete
        assert catalog._is_weather_like(ds) is False


class TestLoad:
    def test_load_populates_repo(self):
        ods = MagicMock()
        ods.catalog_datasets_iter.return_value = iter([
            _make_weather_dataset("01-station-meteo-toulouse-test"),
        ])
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        catalog.load()

        stations = repo.list_stations()
        assert len(stations) == 1
        assert stations[0].id == "01-station-meteo-toulouse-test"

    def test_load_filters_non_weather(self):
        ods = MagicMock()
        ods.catalog_datasets_iter.return_value = iter([
            _make_weather_dataset(),
            _make_non_weather_dataset(),
        ])
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        catalog.load()

        assert len(repo.list_stations()) == 1


class TestDatasets:
    def test_datasets_returns_detected(self):
        ods = MagicMock()
        ods.catalog_datasets_iter.return_value = iter([
            _make_weather_dataset(),
        ])
        repo = WeatherRepositoryMemory()
        catalog = StationCatalogSimple(ods, repo)
        catalog.load()

        datasets = catalog.datasets()
        assert len(datasets) == 1
        assert datasets[0]["dataset_id"] == "01-station-meteo-toulouse-test"
