"""
Repository Pattern: Stockage en memoire des stations et observations.

Utilise des HashMap et LinkedList personnalises pour le stockage
au lieu des dictionnaires Python natifs.
"""

from __future__ import annotations

from datetime import datetime

from meteo_toulouse.data_structures import HashMap, LinkedList
from meteo_toulouse.models import Station, WeatherRecord


class WeatherRepositoryMemory:
    """
    Repository Pattern: Stockage en memoire des stations et observations.

    Utilise des HashMap personnalises pour le stockage au lieu des
    dictionnaires Python natifs.

    Attributes:
        _stations: HashMap[str, Station] - stations indexees par ID.
        _records: HashMap[str, LinkedList[WeatherRecord]] - observations par station.
    """

    def __init__(self) -> None:
        """Initialise le repository avec des HashMap vides."""
        self._stations: HashMap[str, Station] = HashMap()
        self._records: HashMap[str, LinkedList[WeatherRecord]] = HashMap()

    def upsert_station(self, st: Station) -> None:
        """
        Insere ou met a jour une station.

        Args:
            st: Station a inserer/mettre a jour.
        """
        self._stations.put(st.id, st)
        if not self._records.contains(st.id):
            self._records.put(st.id, LinkedList())

    def get_station(self, station_id: str) -> Station | None:
        """
        Recupere une station par son ID.

        Args:
            station_id: ID de la station.

        Returns:
            La station ou None si non trouvee.
        """
        return self._stations.get(station_id)

    def list_stations(self) -> list[Station]:
        """
        Liste toutes les stations.

        Returns:
            Liste des stations enregistrees.
        """
        return self._stations.values()

    def add_record(self, station_id: str, rec: WeatherRecord) -> None:
        """
        Ajoute une observation pour une station.

        Args:
            station_id: ID de la station.
            rec: Observation a ajouter.
        """
        records_list = self._records.get(station_id)
        if records_list is None:
            records_list = LinkedList()
            self._records.put(station_id, records_list)
        records_list.append(rec)

    def latest_records(self, station_id: str, n: int = 5) -> list[WeatherRecord]:
        """
        Recupere les N observations les plus recentes d'une station.

        Args:
            station_id: ID de la station.
            n: Nombre d'observations a retourner.

        Returns:
            Liste des observations triees par date decroissante.
        """
        records_list = self._records.get(station_id)
        if records_list is None:
            return []

        # Convertir en liste et trier
        arr = records_list.to_list()
        arr = sorted(arr, key=lambda r: r.timestamp or datetime.min, reverse=True)
        return arr[:n]
