"""Repository avec cache TTL pour les observations météo.

Ce module fournit un repository qui étend WeatherRepositoryMemory
avec un système de cache à durée de vie limitée (TTL - Time To Live).
Cela permet d'éviter de recharger les observations d'une station
si elles ont été consultées récemment.
"""

from datetime import datetime, timedelta
from meteo_toulouse.repository import WeatherRepositoryMemory


class CachedWeatherRepository(WeatherRepositoryMemory):
    """Repository avec cache TTL pour les observations météo.

    Ce repository hérite de WeatherRepositoryMemory et ajoute un mécanisme
    de cache avec TTL (Time To Live). Lorsqu'une station est chargée,
    l'horodatage est enregistré. Si la station est demandée à nouveau
    avant l'expiration du TTL, le cache est considéré comme valide.

    Attributes:
        _ttl: Durée de vie du cache (timedelta)
        _last_load: Dictionnaire stockant l'horodatage du dernier chargement
                   pour chaque station (station_id -> datetime)

    Example:
        >>> repo = CachedWeatherRepository(ttl_seconds=300)  # Cache de 5 min
        >>> repo.upsert_station(station)
        >>> repo.mark_refreshed(station.id)
        >>> if repo.needs_refresh(station.id):
        ...     # Recharger les données
        ...     pass
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialise le repository avec un cache TTL.

        Args:
            ttl_seconds: Durée de vie du cache en secondes (défaut: 300 = 5 minutes)
        """
        super().__init__()
        self._ttl = timedelta(seconds=ttl_seconds)
        self._last_load: dict[str, datetime] = {}

    def needs_refresh(self, station_id: str) -> bool:
        """Vérifie si le cache pour une station est expiré.

        Args:
            station_id: Identifiant unique de la station

        Returns:
            True si le cache est expiré ou inexistant, False sinon

        Example:
            >>> repo = CachedWeatherRepository(ttl_seconds=60)
            >>> repo.needs_refresh("station-1")
            True  # Jamais chargé
            >>> repo.mark_refreshed("station-1")
            >>> repo.needs_refresh("station-1")
            False  # Cache valide
        """
        if station_id not in self._last_load:
            return True

        elapsed = datetime.now() - self._last_load[station_id]
        return elapsed > self._ttl

    def mark_refreshed(self, station_id: str) -> None:
        """Marque une station comme récemment chargée.

        Met à jour l'horodatage du dernier chargement pour la station.
        Cela réinitialise le TTL du cache.

        Args:
            station_id: Identifiant unique de la station

        Example:
            >>> repo = CachedWeatherRepository()
            >>> repo.mark_refreshed("station-1")
            >>> repo.needs_refresh("station-1")
            False
        """
        self._last_load[station_id] = datetime.now()

    def clear_cache(self, station_id: str | None = None) -> None:
        """Vide le cache pour une station ou toutes les stations.

        Args:
            station_id: Identifiant de la station (None = toutes les stations)

        Example:
            >>> repo = CachedWeatherRepository()
            >>> repo.mark_refreshed("station-1")
            >>> repo.clear_cache("station-1")
            >>> repo.needs_refresh("station-1")
            True
            >>> repo.clear_cache()  # Vide tout le cache
        """
        if station_id is None:
            self._last_load.clear()
        elif station_id in self._last_load:
            del self._last_load[station_id]

    def get_cache_info(self, station_id: str) -> dict[str, str | bool]:
        """Retourne les informations sur l'état du cache pour une station.

        Args:
            station_id: Identifiant unique de la station

        Returns:
            Dictionnaire contenant:
                - cached: True si la station est en cache
                - last_load: Horodatage du dernier chargement (str ou None)
                - time_remaining: Temps restant avant expiration (str ou None)
                - expired: True si le cache est expiré

        Example:
            >>> repo = CachedWeatherRepository(ttl_seconds=300)
            >>> info = repo.get_cache_info("station-1")
            >>> info["cached"]
            False
        """
        if station_id not in self._last_load:
            return {
                "cached": False,
                "last_load": None,
                "time_remaining": None,
                "expired": True,
            }

        last_load = self._last_load[station_id]
        elapsed = datetime.now() - last_load
        remaining = self._ttl - elapsed
        expired = remaining.total_seconds() <= 0

        return {
            "cached": True,
            "last_load": last_load.isoformat(),
            "time_remaining": str(remaining) if not expired else "expired",
            "expired": expired,
        }
