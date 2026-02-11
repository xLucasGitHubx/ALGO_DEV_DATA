"""Tests pour le service WeatherQueryService."""

from datetime import datetime
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.services.query import WeatherQueryService


class TestLatestForStation:
    def test_returns_records(self):
        repo = WeatherRepositoryMemory()
        st = Station(id="st-01", name="Test", dataset_id="st-01")
        repo.upsert_station(st)
        repo.add_record("st-01", WeatherRecord(
            station_id="st-01",
            temperature_c=20.0,
            timestamp=datetime(2024, 1, 1),
        ))

        svc = WeatherQueryService(repo)
        result = svc.latest_for_station("st-01", n=5)
        assert len(result) == 1
        assert result[0].temperature_c == 20.0

    def test_default_n_is_one(self):
        repo = WeatherRepositoryMemory()
        st = Station(id="st-01", name="Test", dataset_id="st-01")
        repo.upsert_station(st)
        repo.add_record("st-01", WeatherRecord(
            station_id="st-01", timestamp=datetime(2024, 1, 1),
        ))
        repo.add_record("st-01", WeatherRecord(
            station_id="st-01", timestamp=datetime(2024, 1, 2),
        ))

        svc = WeatherQueryService(repo)
        result = svc.latest_for_station("st-01")
        assert len(result) == 1

    def test_empty_station(self):
        repo = WeatherRepositoryMemory()
        svc = WeatherQueryService(repo)
        result = svc.latest_for_station("missing")
        assert result == []
