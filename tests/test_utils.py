"""Tests pour le module utils."""

from datetime import datetime
from meteo_toulouse.utils import norm, parse_datetime_any


class TestNorm:
    def test_lowercase(self):
        assert norm("HELLO") == "hello"

    def test_accents_removed(self):
        assert norm("cafe") == "cafe"
        assert norm("temperature") == "temperature"

    def test_accents_e(self):
        # e avec accent aigu
        assert norm("\u00e9") == "e"

    def test_strip_whitespace(self):
        assert norm("  hello  ") == "hello"

    def test_none_returns_empty(self):
        assert norm(None) == ""

    def test_non_string_coerced(self):
        assert norm(42) == "42"

    def test_empty_string(self):
        assert norm("") == ""


class TestParseDatetimeAny:
    def test_none_returns_none(self):
        assert parse_datetime_any(None) is None

    def test_empty_string_returns_none(self):
        assert parse_datetime_any("") is None
        assert parse_datetime_any("  ") is None

    def test_invalid_returns_none(self):
        assert parse_datetime_any("not a date") is None

    def test_datetime_passthrough(self):
        dt = datetime(2024, 1, 15, 10, 30)
        assert parse_datetime_any(dt) is dt

    def test_iso_format(self):
        result = parse_datetime_any("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_iso_with_microseconds(self):
        result = parse_datetime_any("2024-01-15T10:30:00.123456")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_date_only(self):
        result = parse_datetime_any("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_space_separated(self):
        result = parse_datetime_any("2024-01-15 10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_z_suffix(self):
        result = parse_datetime_any("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024

    def test_integer_returns_none(self):
        # Un entier converti en string ne matche aucun format
        assert parse_datetime_any(12345) is None
