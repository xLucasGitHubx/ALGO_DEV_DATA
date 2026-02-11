"""
Configuration et constantes de l'application.

Centralise tous les parametres configurables: URLs, timeouts,
limites de pagination, et la configuration globale APP_CONFIG.
"""

from __future__ import annotations

import os
from typing import TypeVar, Generic, Callable  # noqa: F401 - re-exported

# ============================================================
# CONSTANTES
# ============================================================

DEFAULT_BASE_URL = os.environ.get(
    "ODS_BASE_URL",
    "https://data.toulouse-metropole.fr/api/explore/v2.1",
)

HTTP_TIMEOUT = 20
CATALOG_PAGE_SIZE = 100
CATALOG_HARD_LIMIT = 10_000
RECORDS_PAGE_SIZE = 100
PRINT_WIDTH = 110

JSONLike = dict[str, object]

APP_CONFIG: dict[str, object] = {
    "base_url": DEFAULT_BASE_URL,
    "catalog": {
        "hard_limit": CATALOG_HARD_LIMIT,
    },
    "ingestion": {
        "max_rows_per_station": 5,
        "max_stations": None,
    },
    "ui": {
        "enable_carousel": True,
        "carousel_delay_sec": 5,
    },
}

# ============================================================
# TYPE VARIABLES (utilisees par les structures de donnees)
# ============================================================

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
