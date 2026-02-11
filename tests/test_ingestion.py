"""Tests pour le service WeatherIngestionService (avec mocks)."""

from unittest.mock import MagicMock, patch
import requests
from meteo_toulouse.models import Station
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.cleaner import BasicCleaner
from meteo_toulouse.services.ingestion import WeatherIngestionService


def _make_station(sid: str = "st-01") -> Station:
    return Station(id=sid, name="Test", dataset_id=sid)


class TestIngestLatest:
    def test_ingest_records(self):
        ods = MagicMock()
        ods.dataset_info.return_value = {
            "fields": [{"name": "date_observation", "type": "datetime"}]
        }
        ods.iter_records.return_value = iter([
            {"temperature": 20.0, "date_observation": "2024-01-15T10:00:00"},
            {"temperature": 21.0, "date_observation": "2024-01-15T11:00:00"},
        ])

        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)

        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        count = svc.ingest_latest(st, max_rows=5)

        assert count == 2
        records = repo.latest_records("st-01")
        assert len(records) == 2

    def test_ingest_empty_dataset_id(self):
        ods = MagicMock()
        repo = WeatherRepositoryMemory()
        st = Station(id="x", name="X", dataset_id="")
        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        assert svc.ingest_latest(st) == 0

    def test_ingest_http_error_handled(self):
        ods = MagicMock()
        ods.dataset_info.side_effect = requests.HTTPError("404")
        ods.iter_records.side_effect = requests.HTTPError("500")

        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)

        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        count = svc.ingest_latest(st)
        assert count == 0


class TestIngestAllLatest:
    def test_ingest_all(self):
        ods = MagicMock()
        ods.dataset_info.return_value = {"fields": []}
        # iter_records est appele plusieurs fois, chaque appel doit retourner un nouvel iterateur
        ods.iter_records.side_effect = lambda **kwargs: iter([{"tair": 20.0}])

        repo = WeatherRepositoryMemory()
        repo.upsert_station(_make_station("a"))
        repo.upsert_station(_make_station("b"))

        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        total = svc.ingest_all_latest(max_rows_per_station=1)
        assert total == 2

    def test_ingest_all_max_stations(self):
        ods = MagicMock()
        ods.dataset_info.return_value = {"fields": []}
        ods.iter_records.side_effect = lambda **kwargs: iter([{"tair": 20.0}])

        repo = WeatherRepositoryMemory()
        for i in range(5):
            repo.upsert_station(_make_station(f"st-{i}"))

        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        total = svc.ingest_all_latest(max_rows_per_station=1, max_stations=2)
        assert total == 2


class TestFindFirstDateField:
    def test_finds_date_field(self):
        ods = MagicMock()
        ods.dataset_info.return_value = {
            "fields": [
                {"name": "temperature", "type": "double"},
                {"name": "date_observation", "type": "datetime"},
            ]
        }
        repo = WeatherRepositoryMemory()
        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        result = svc._find_first_date_field("test-ds")
        assert result == "date_observation"

    def test_no_date_field(self):
        ods = MagicMock()
        ods.dataset_info.return_value = {
            "fields": [{"name": "temperature", "type": "double"}]
        }
        repo = WeatherRepositoryMemory()
        svc = WeatherIngestionService(ods, repo, BasicCleaner())
        result = svc._find_first_date_field("test-ds")
        assert result is None
