"""Tests pour le BasicCleaner."""

from meteo_toulouse.cleaner import BasicCleaner


class TestGetFirst:
    def test_exact_match(self):
        cleaner = BasicCleaner()
        data = {"temperature": 20.0, "humidity": 65.0}
        result = cleaner._get_first(data, ["temperature"])
        assert result == 20.0

    def test_partial_match(self):
        cleaner = BasicCleaner()
        data = {"temperature_celsius": 20.0}
        result = cleaner._get_first(data, ["temperature"])
        assert result == 20.0

    def test_no_match(self):
        cleaner = BasicCleaner()
        data = {"wind_speed": 5.0}
        result = cleaner._get_first(data, ["temperature"])
        assert result is None

    def test_first_key_wins(self):
        cleaner = BasicCleaner()
        data = {"temp": 18.0, "temperature": 20.0}
        result = cleaner._get_first(data, ["temperature", "temp"])
        assert result == 20.0


class TestToFloat:
    def test_valid_float(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float(20.5) == 20.5

    def test_string_float(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float("20.5") == 20.5

    def test_comma_decimal(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float("12,5") == 12.5

    def test_none(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float(None) is None

    def test_empty_string(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float("") is None

    def test_invalid(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float("abc") is None

    def test_integer(self):
        cleaner = BasicCleaner()
        assert cleaner._to_float(20) == 20.0


class TestClean:
    def test_clean_full_record(self):
        cleaner = BasicCleaner()
        raw = {
            "temperature": 20.5,
            "humidity": 65.0,
            "pressure": 1013.0,
            "wind_speed": 3.2,
            "wind_dir": 180.0,
            "rain": 0.5,
            "date_observation": "2024-01-15T10:30:00",
        }
        rec = cleaner.clean(raw, "st-01")
        assert rec.station_id == "st-01"
        assert rec.temperature_c == 20.5
        assert rec.humidity_pct == 65.0
        assert rec.pressure_hpa == 1013.0
        assert rec.wind_speed_ms == 3.2
        assert rec.wind_dir_deg == 180.0
        assert rec.rain_mm == 0.5
        assert rec.timestamp is not None
        assert rec.raw == raw

    def test_clean_partial_record(self):
        cleaner = BasicCleaner()
        raw = {"tair": 20.5}
        rec = cleaner.clean(raw, "st-01")
        assert rec.temperature_c == 20.5
        assert rec.humidity_pct is None
        assert rec.pressure_hpa is None
        assert rec.timestamp is None

    def test_clean_alternative_keys(self):
        cleaner = BasicCleaner()
        raw = {"temp": 18.0, "hum": 70.0, "ff": 5.0}
        rec = cleaner.clean(raw, "st-01")
        assert rec.temperature_c == 18.0
        assert rec.humidity_pct == 70.0
        assert rec.wind_speed_ms == 5.0

    def test_clean_empty_raw(self):
        cleaner = BasicCleaner()
        raw = {}
        rec = cleaner.clean(raw, "st-01")
        assert rec.station_id == "st-01"
        assert rec.temperature_c is None
        assert rec.timestamp is None
