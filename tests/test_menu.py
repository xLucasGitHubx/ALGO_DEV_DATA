"""Tests pour le StationSelectorMenu (avec mocks sur input)."""

from datetime import datetime
from unittest.mock import patch
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.services.forecast import ForecastService
from meteo_toulouse.services.query import WeatherQueryService
from meteo_toulouse.ui.menu import StationSelectorMenu


def _make_repo() -> WeatherRepositoryMemory:
    repo = WeatherRepositoryMemory()
    for i in range(3):
        st = Station(id=f"st-{i}", name=f"Station {i} Meteo", dataset_id=f"st-{i}")
        repo.upsert_station(st)
        repo.add_record(f"st-{i}", WeatherRecord(
            station_id=f"st-{i}",
            temperature_c=20.0 + i,
            timestamp=datetime(2024, 1, i + 1),
        ))
    return repo


def _make_menu(repo: WeatherRepositoryMemory | None = None) -> StationSelectorMenu:
    if repo is None:
        repo = _make_repo()
    fc = ForecastService(repo)
    query = WeatherQueryService(repo)
    return StationSelectorMenu(repo=repo, forecast=fc, query=query)


class TestRefreshStations:
    def test_refresh_populates_list(self):
        menu = _make_menu()
        menu._refresh_stations()
        assert len(menu._stations_list) == 3


class TestSearchStation:
    def test_search_found(self):
        menu = _make_menu()
        menu._refresh_stations()
        results = menu._search_station("Station 1")
        assert len(results) == 1
        assert results[0][1].name == "Station 1 Meteo"

    def test_search_partial(self):
        menu = _make_menu()
        menu._refresh_stations()
        results = menu._search_station("meteo")
        assert len(results) == 3

    def test_search_no_match(self):
        menu = _make_menu()
        menu._refresh_stations()
        results = menu._search_station("xyz_not_found")
        assert len(results) == 0

    def test_search_case_insensitive(self):
        menu = _make_menu()
        menu._refresh_stations()
        results = menu._search_station("STATION")
        assert len(results) == 3


class TestRun:
    @patch("builtins.input", return_value="Q")
    def test_quit(self, mock_input, capsys):
        menu = _make_menu()
        menu.run()
        output = capsys.readouterr().out
        assert "Au revoir" in output

    @patch("builtins.input", side_effect=["X", "", "Q"])
    def test_invalid_then_quit(self, mock_input, capsys):
        menu = _make_menu()
        menu.run()
        output = capsys.readouterr().out
        assert "Option non reconnue" in output

    def test_empty_repo(self, capsys):
        repo = WeatherRepositoryMemory()
        menu = _make_menu(repo)
        menu.run()
        output = capsys.readouterr().out
        assert "Aucune station" in output
