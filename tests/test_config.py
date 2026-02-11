"""Tests pour le module config."""

from meteo_toulouse.config import (
    DEFAULT_BASE_URL,
    HTTP_TIMEOUT,
    CATALOG_PAGE_SIZE,
    CATALOG_HARD_LIMIT,
    RECORDS_PAGE_SIZE,
    PRINT_WIDTH,
    APP_CONFIG,
    JSONLike,
)


def test_default_base_url_is_string():
    assert isinstance(DEFAULT_BASE_URL, str)
    assert DEFAULT_BASE_URL.startswith("http")


def test_constants_positive():
    assert HTTP_TIMEOUT > 0
    assert CATALOG_PAGE_SIZE > 0
    assert CATALOG_HARD_LIMIT > 0
    assert RECORDS_PAGE_SIZE > 0
    assert PRINT_WIDTH > 0


def test_app_config_keys():
    assert "base_url" in APP_CONFIG
    assert "catalog" in APP_CONFIG
    assert "ingestion" in APP_CONFIG
    assert "ui" in APP_CONFIG


def test_app_config_catalog():
    catalog_cfg = APP_CONFIG["catalog"]
    assert "hard_limit" in catalog_cfg


def test_app_config_ingestion():
    ingestion_cfg = APP_CONFIG["ingestion"]
    assert "max_rows_per_station" in ingestion_cfg
    assert "max_stations" in ingestion_cfg


def test_app_config_ui():
    ui_cfg = APP_CONFIG["ui"]
    assert "enable_carousel" in ui_cfg
    assert "carousel_delay_sec" in ui_cfg


def test_jsonlike_is_dict_type():
    # JSONLike est un alias pour dict[str, object]
    sample: JSONLike = {"key": "value"}
    assert isinstance(sample, dict)
