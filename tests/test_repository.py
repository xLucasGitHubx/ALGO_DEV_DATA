"""Tests pour le repository WeatherRepositoryMemory."""

from datetime import datetime
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory


def _make_station(sid: str = "st-01", name: str = "Test Station") -> Station:
    return Station(id=sid, name=name, dataset_id=sid)


def _make_record(sid: str = "st-01", temp: float = 20.0, ts: datetime | None = None) -> WeatherRecord:
    return WeatherRecord(station_id=sid, temperature_c=temp, timestamp=ts)


class TestUpsertStation:
    def test_insert_new(self):
        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)
        assert repo.get_station("st-01") == st

    def test_update_existing(self):
        repo = WeatherRepositoryMemory()
        st1 = _make_station(name="Original")
        repo.upsert_station(st1)
        st2 = _make_station(name="Updated")
        repo.upsert_station(st2)
        result = repo.get_station("st-01")
        assert result.name == "Updated"


class TestGetStation:
    def test_get_existing(self):
        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)
        assert repo.get_station("st-01") is not None

    def test_get_nonexistent(self):
        repo = WeatherRepositoryMemory()
        assert repo.get_station("missing") is None


class TestListStations:
    def test_list_empty(self):
        repo = WeatherRepositoryMemory()
        assert repo.list_stations() == []

    def test_list_multiple(self):
        repo = WeatherRepositoryMemory()
        repo.upsert_station(_make_station("a", "Station A"))
        repo.upsert_station(_make_station("b", "Station B"))
        stations = repo.list_stations()
        assert len(stations) == 2
        ids = {s.id for s in stations}
        assert ids == {"a", "b"}


class TestAddRecord:
    def test_add_record(self):
        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)
        rec = _make_record()
        repo.add_record("st-01", rec)
        records = repo.latest_records("st-01")
        assert len(records) == 1
        assert records[0].temperature_c == 20.0

    def test_add_record_auto_creates_list(self):
        repo = WeatherRepositoryMemory()
        # Pas de station creee, mais on ajoute un record
        rec = _make_record(sid="new")
        repo.add_record("new", rec)
        records = repo.latest_records("new")
        assert len(records) == 1


class TestLatestRecords:
    def test_empty_station(self):
        repo = WeatherRepositoryMemory()
        assert repo.latest_records("missing") == []

    def test_sorted_by_timestamp_desc(self):
        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)

        repo.add_record("st-01", _make_record(ts=datetime(2024, 1, 1)))
        repo.add_record("st-01", _make_record(ts=datetime(2024, 1, 3)))
        repo.add_record("st-01", _make_record(ts=datetime(2024, 1, 2)))

        records = repo.latest_records("st-01", n=3)
        timestamps = [r.timestamp for r in records]
        assert timestamps == [datetime(2024, 1, 3), datetime(2024, 1, 2), datetime(2024, 1, 1)]

    def test_limit_n(self):
        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)

        for i in range(10):
            repo.add_record("st-01", _make_record(ts=datetime(2024, 1, i + 1)))

        records = repo.latest_records("st-01", n=3)
        assert len(records) == 3

    def test_none_timestamps_handled(self):
        repo = WeatherRepositoryMemory()
        st = _make_station()
        repo.upsert_station(st)

        repo.add_record("st-01", _make_record(ts=None))
        repo.add_record("st-01", _make_record(ts=datetime(2024, 1, 1)))

        records = repo.latest_records("st-01", n=5)
        assert len(records) == 2
        # Le record avec timestamp vient en premier
        assert records[0].timestamp == datetime(2024, 1, 1)
