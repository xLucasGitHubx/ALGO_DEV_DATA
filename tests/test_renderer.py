"""Tests pour le SimpleRenderer (capture stdout)."""

from datetime import datetime
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.ui.renderer import SimpleRenderer


class TestPrintDatasets:
    def test_empty_datasets(self, capsys):
        SimpleRenderer.print_datasets([])
        output = capsys.readouterr().out
        assert "aucune station" in output.lower()

    def test_with_datasets(self, capsys):
        datasets = [{
            "dataset_id": "test-ds",
            "metas": {"default": {"title": "Test", "records_count": 100}},
        }]
        SimpleRenderer.print_datasets(datasets)
        output = capsys.readouterr().out
        assert "test-ds" in output
        assert "100" in output


class TestPrintLatest:
    def test_with_records(self, capsys):
        repo = WeatherRepositoryMemory()
        st = Station(id="st-01", name="Test Station", dataset_id="st-01")
        repo.upsert_station(st)
        repo.add_record("st-01", WeatherRecord(
            station_id="st-01",
            temperature_c=20.0,
            humidity_pct=65.0,
            timestamp=datetime(2024, 1, 15, 10, 0),
        ))
        SimpleRenderer.print_latest(repo)
        output = capsys.readouterr().out
        assert "Test Station" in output
        assert "20.0" in output

    def test_no_records(self, capsys):
        repo = WeatherRepositoryMemory()
        st = Station(id="st-01", name="Empty Station", dataset_id="st-01")
        repo.upsert_station(st)
        SimpleRenderer.print_latest(repo)
        output = capsys.readouterr().out
        assert "Empty Station" in output
        assert "derniere obs: -" in output


class TestPrintStationDetail:
    def test_with_records_and_forecast(self, capsys):
        st = Station(id="st-01", name="Test Station", dataset_id="ds-01")
        records = [WeatherRecord(
            station_id="st-01",
            temperature_c=20.0,
            humidity_pct=65.0,
            wind_speed_ms=3.0,
            rain_mm=0.0,
            timestamp=datetime(2024, 1, 15, 10, 0),
        )]
        SimpleRenderer.print_station_detail(st, records, forecast=20.0)
        output = capsys.readouterr().out
        assert "Test Station" in output
        assert "20.0" in output
        assert "Prevision" in output

    def test_no_records(self, capsys):
        st = Station(id="st-01", name="Test Station", dataset_id="ds-01")
        SimpleRenderer.print_station_detail(st, [], forecast=None)
        output = capsys.readouterr().out
        assert "Aucune observation" in output
        assert "Donnees insuffisantes" in output

    def test_no_forecast(self, capsys):
        st = Station(id="st-01", name="Test Station", dataset_id="ds-01")
        records = [WeatherRecord(
            station_id="st-01",
            temperature_c=20.0,
            timestamp=datetime(2024, 1, 15),
        )]
        SimpleRenderer.print_station_detail(st, records, forecast=None)
        output = capsys.readouterr().out
        assert "Donnees insuffisantes" in output
