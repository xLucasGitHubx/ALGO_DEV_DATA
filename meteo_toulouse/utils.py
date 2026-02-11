"""
Utilitaires: normalisation de texte et parsing de dates.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime


def norm(s: str) -> str:
    """
    Normalise un texte: minuscule + suppression accents + trim.

    Args:
        s: Chaine a normaliser.

    Returns:
        Chaine normalisee.
    """
    if not isinstance(s, str):
        s = "" if s is None else str(s)
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


def parse_datetime_any(x: object | None) -> datetime | None:
    """
    Parse divers formats date/datetime retournes par ODS.

    Args:
        x: Valeur a parser (string, datetime, ou None).

    Returns:
        Objet datetime ou None si parsing impossible.
    """
    if x is None:
        return None
    if isinstance(x, datetime):
        return x
    s = str(x).strip()
    if not s:
        return None

    candidates = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in candidates:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    # Derniere chance: enlever le fuseau si present
    if s.endswith("Z"):
        try:
            return datetime.strptime(s[:-1], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                return datetime.strptime(s[:-1], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass

    return None
