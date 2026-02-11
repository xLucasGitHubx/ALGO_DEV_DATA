"""Tests pour le service ForecastService."""

from datetime import datetime
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.services.forecast import ForecastService


def _setup_repo_with_records(temps: list[float | None]) -> WeatherRepositoryMemory:
    """Cree un repo avec des records de temperature."""
    repo = WeatherRepositoryMemory()
    st = Station(id="st-01", name="Test", dataset_id="st-01")
    repo.upsert_station(st)
    for i, t in enumerate(temps):
        repo.add_record("st-01", WeatherRecord(
            station_id="st-01",
            temperature_c=t,
            timestamp=datetime(2024, 1, i + 1),
        ))
    return repo


class TestForecastStationTemp:
    def test_average_calculation(self):
        repo = _setup_repo_with_records([20.0, 22.0, 24.0])
        svc = ForecastService(repo)
        result = svc.forecast_station_temp("st-01", last_n=3)
        assert result == pytest.approx(22.0)

    def test_no_data_returns_none(self):
        repo = WeatherRepositoryMemory()
        svc = ForecastService(repo)
        result = svc.forecast_station_temp("missing")
        assert result is None

    def test_none_temperatures_skipped(self):
        repo = _setup_repo_with_records([20.0, None, 24.0])
        svc = ForecastService(repo)
        result = svc.forecast_station_temp("st-01", last_n=3)
        assert result == pytest.approx(22.0)

    def test_all_none_returns_none(self):
        repo = _setup_repo_with_records([None, None, None])
        svc = ForecastService(repo)
        result = svc.forecast_station_temp("st-01", last_n=3)
        assert result is None

    def test_single_record(self):
        repo = _setup_repo_with_records([15.0])
        svc = ForecastService(repo)
        result = svc.forecast_station_temp("st-01", last_n=1)
        assert result == pytest.approx(15.0)


import pytest
