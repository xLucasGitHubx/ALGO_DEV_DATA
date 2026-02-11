"""Tests pour les modeles de domaine Station et WeatherRecord."""

from datetime import datetime
from meteo_toulouse.models import Station, WeatherRecord


class TestStation:
    def test_creation(self):
        st = Station(id="01", name="Test Station", dataset_id="ds-01")
        assert st.id == "01"
        assert st.name == "Test Station"
        assert st.dataset_id == "ds-01"

    def test_default_meta(self):
        st = Station(id="01", name="Test", dataset_id="ds-01")
        assert st.meta == {}

    def test_custom_meta(self):
        meta = {"key": "value"}
        st = Station(id="01", name="Test", dataset_id="ds-01", meta=meta)
        assert st.meta == {"key": "value"}

    def test_equality(self):
        st1 = Station(id="01", name="Test", dataset_id="ds-01")
        st2 = Station(id="01", name="Test", dataset_id="ds-01")
        assert st1 == st2

    def test_inequality(self):
        st1 = Station(id="01", name="Test", dataset_id="ds-01")
        st2 = Station(id="02", name="Other", dataset_id="ds-02")
        assert st1 != st2


class TestWeatherRecord:
    def test_creation_minimal(self):
        rec = WeatherRecord(station_id="st-01")
        assert rec.station_id == "st-01"
        assert rec.timestamp is None
        assert rec.temperature_c is None
        assert rec.humidity_pct is None
        assert rec.pressure_hpa is None
        assert rec.wind_speed_ms is None
        assert rec.wind_dir_deg is None
        assert rec.rain_mm is None
        assert rec.raw == {}

    def test_creation_full(self):
        ts = datetime(2024, 1, 15, 10, 30)
        rec = WeatherRecord(
            station_id="st-01",
            timestamp=ts,
            temperature_c=15.5,
            humidity_pct=72.0,
            pressure_hpa=1013.25,
            wind_speed_ms=3.2,
            wind_dir_deg=180.0,
            rain_mm=0.5,
            raw={"test": True},
        )
        assert rec.temperature_c == 15.5
        assert rec.humidity_pct == 72.0
        assert rec.pressure_hpa == 1013.25
        assert rec.wind_speed_ms == 3.2
        assert rec.wind_dir_deg == 180.0
        assert rec.rain_mm == 0.5
        assert rec.raw == {"test": True}

    def test_partial_data(self):
        rec = WeatherRecord(
            station_id="st-01",
            temperature_c=20.0,
        )
        assert rec.temperature_c == 20.0
        assert rec.humidity_pct is None
