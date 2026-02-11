"""Tests pour le StationCarouselRenderer."""

from datetime import datetime
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.services.forecast import ForecastService
from meteo_toulouse.ui.carousel import StationCarouselRenderer


def _make_repo_with_station() -> WeatherRepositoryMemory:
    repo = WeatherRepositoryMemory()
    st = Station(id="st-01", name="Test Station", dataset_id="st-01")
    repo.upsert_station(st)
    repo.add_record("st-01", WeatherRecord(
        station_id="st-01",
        temperature_c=20.0,
        humidity_pct=65.0,
        wind_speed_ms=3.0,
        rain_mm=0.0,
        timestamp=datetime(2024, 1, 15, 10, 0),
    ))
    return repo


class TestLoadStationsToQueue:
    def test_stations_loaded(self):
        repo = _make_repo_with_station()
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc, delay_seconds=1)
        carousel._load_stations_to_queue()
        assert carousel._queue.size() == 1

    def test_empty_repo(self):
        repo = WeatherRepositoryMemory()
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc)
        carousel._load_stations_to_queue()
        assert carousel._queue.is_empty()


class TestFormatRecordLine:
    def test_with_data(self):
        repo = _make_repo_with_station()
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc)
        st = repo.list_stations()[0]
        line = carousel._format_record_line(st)
        assert "Test Station" in line
        assert "20.0" in line

    def test_no_data(self):
        repo = WeatherRepositoryMemory()
        st = Station(id="empty", name="Empty", dataset_id="empty")
        repo.upsert_station(st)
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc)
        line = carousel._format_record_line(st)
        assert "Aucune observation" in line


class TestFormatForecastLine:
    def test_with_forecast(self):
        repo = _make_repo_with_station()
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc)
        st = repo.list_stations()[0]
        line = carousel._format_forecast_line(st)
        assert "20.00" in line

    def test_no_forecast(self):
        repo = WeatherRepositoryMemory()
        st = Station(id="empty", name="Empty", dataset_id="empty")
        repo.upsert_station(st)
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc)
        line = carousel._format_forecast_line(st)
        assert "indisponible" in line


class TestRun:
    def test_run_empty_queue(self, capsys):
        repo = WeatherRepositoryMemory()
        fc = ForecastService(repo)
        carousel = StationCarouselRenderer(repo, fc)
        carousel.run()
        output = capsys.readouterr().out
        assert "Aucune station" in output
