"""
meteo_toulouse_app.py
============================================================
Application Meteo Toulouse Metropole - Version Complete

Ce fichier contient l'implementation complete de l'application meteo
avec toutes les structures de donnees personnalisees requises:
- Liste chainee (LinkedList)
- File (Queue)
- Table de hachage avec chainage (HashMap)

Design Patterns utilises:
- Repository Pattern: WeatherRepositoryMemory
- Service Layer Pattern: IngestionService, QueryService, ForecastService
- Client/Adapter Pattern: ODSClient
- Factory Pattern: BasicCleaner
- Command Pattern: Menu interactif
- Strategy Pattern: Differents renderers

Python 3.12+
============================================================
"""

from __future__ import annotations

import os
import sys
import time
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeVar, Generic, Callable

import requests

# ============================================================
# CONSTANTES ET CONFIGURATION
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
# STRUCTURES DE DONNEES PERSONNALISEES
# ============================================================

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# ------------------------------------------------------------
# Structure de donnees: Liste Chainee (Linked List)
# ------------------------------------------------------------

class ListNode(Generic[T]):
    """
    Noeud d'une liste chainee.

    Attributes:
        value: La valeur stockee dans le noeud.
        next: Reference vers le noeud suivant (ou None si dernier).
    """

    def __init__(self, value: T) -> None:
        self.value: T = value
        self.next: ListNode[T] | None = None

    def __repr__(self) -> str:
        return f"ListNode({self.value!r})"


class LinkedList(Generic[T]):
    """
    Structure de donnees: Liste Chainee (Linked List)

    Implementation d'une liste chainee simple avec operations de base.
    Utilisee pour stocker les stations meteo et comme base pour la Queue
    et le HashMap (chainage pour collisions).

    Complexite:
        - append: O(n) - parcours jusqu'a la fin
        - prepend: O(1) - insertion en tete
        - remove: O(n) - recherche + suppression
        - __contains__: O(n) - recherche lineaire
        - __len__: O(n) - comptage des noeuds
        - __iter__: O(n) - parcours complet

    Attributes:
        head: Premier noeud de la liste (ou None si vide).
    """

    def __init__(self) -> None:
        """Initialise une liste chainee vide."""
        self._head: ListNode[T] | None = None
        self._size: int = 0

    @property
    def head(self) -> ListNode[T] | None:
        """Retourne le premier noeud de la liste."""
        return self._head

    def is_empty(self) -> bool:
        """Verifie si la liste est vide."""
        return self._head is None

    def append(self, value: T) -> None:
        """
        Ajoute un element a la fin de la liste.

        Args:
            value: Valeur a ajouter.
        """
        new_node = ListNode(value)
        if self._head is None:
            self._head = new_node
        else:
            current = self._head
            while current.next is not None:
                current = current.next
            current.next = new_node
        self._size += 1

    def prepend(self, value: T) -> None:
        """
        Ajoute un element au debut de la liste.

        Args:
            value: Valeur a ajouter.
        """
        new_node = ListNode(value)
        new_node.next = self._head
        self._head = new_node
        self._size += 1

    def remove(self, value: T) -> bool:
        """
        Supprime la premiere occurrence d'une valeur.

        Args:
            value: Valeur a supprimer.

        Returns:
            True si l'element a ete trouve et supprime, False sinon.
        """
        if self._head is None:
            return False

        # Cas special: suppression de la tete
        if self._head.value == value:
            self._head = self._head.next
            self._size -= 1
            return True

        # Recherche dans le reste de la liste
        current = self._head
        while current.next is not None:
            if current.next.value == value:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next

        return False

    def get(self, index: int) -> T | None:
        """
        Recupere l'element a l'index donne.

        Args:
            index: Index de l'element (0-based).

        Returns:
            La valeur a l'index ou None si index invalide.
        """
        if index < 0 or index >= self._size:
            return None

        current = self._head
        for _ in range(index):
            if current is None:
                return None
            current = current.next

        return current.value if current else None

    def find(self, predicate: Callable[[T], bool]) -> T | None:
        """
        Trouve le premier element satisfaisant le predicat.

        Args:
            predicate: Fonction de test retournant True si l'element correspond.

        Returns:
            Le premier element correspondant ou None.
        """
        for item in self:
            if predicate(item):
                return item
        return None

    def to_list(self) -> list[T]:
        """Convertit la liste chainee en liste Python standard."""
        return list(self)

    def __contains__(self, value: T) -> bool:
        """Verifie si une valeur est presente dans la liste."""
        for item in self:
            if item == value:
                return True
        return False

    def __len__(self) -> int:
        """Retourne le nombre d'elements dans la liste."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Iterateur pour parcourir la liste."""
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        elements = [repr(item) for item in self]
        return f"LinkedList([{', '.join(elements)}])"


# ------------------------------------------------------------
# Structure de donnees: File (Queue) - FIFO
# ------------------------------------------------------------

class Queue(Generic[T]):
    """
    Structure de donnees: File (Queue) - First In, First Out

    Implementation d'une file basee sur une liste chainee.
    Utilisee pour le carrousel de stations meteo (parcours cyclique).

    Principe FIFO: Le premier element ajoute est le premier retire.

    Complexite:
        - enqueue: O(1) - insertion en queue (avec pointeur tail)
        - dequeue: O(1) - suppression en tete
        - peek: O(1) - lecture de la tete
        - size: O(1) - compteur maintenu

    Attributes:
        _head: Premier element de la file (prochain a sortir).
        _tail: Dernier element de la file (dernier ajoute).
        _size: Nombre d'elements dans la file.
    """

    def __init__(self) -> None:
        """Initialise une file vide."""
        self._head: ListNode[T] | None = None
        self._tail: ListNode[T] | None = None
        self._size: int = 0

    def enqueue(self, value: T) -> None:
        """
        Ajoute un element a la fin de la file.

        Args:
            value: Valeur a ajouter.
        """
        new_node = ListNode(value)

        if self._tail is None:
            # File vide
            self._head = new_node
            self._tail = new_node
        else:
            # Ajout en fin
            self._tail.next = new_node
            self._tail = new_node

        self._size += 1

    def dequeue(self) -> T | None:
        """
        Retire et retourne l'element en tete de file.

        Returns:
            L'element retire ou None si la file est vide.
        """
        if self._head is None:
            return None

        value = self._head.value
        self._head = self._head.next

        if self._head is None:
            # La file est maintenant vide
            self._tail = None

        self._size -= 1
        return value

    def peek(self) -> T | None:
        """
        Retourne l'element en tete sans le retirer.

        Returns:
            L'element en tete ou None si la file est vide.
        """
        return self._head.value if self._head else None

    def is_empty(self) -> bool:
        """Verifie si la file est vide."""
        return self._head is None

    def size(self) -> int:
        """Retourne le nombre d'elements dans la file."""
        return self._size

    def rotate(self) -> None:
        """
        Rotation: deplace l'element de tete vers la queue.
        Utile pour le carrousel cyclique des stations.
        """
        if self._size <= 1:
            return

        # Deplace la tete vers la queue
        value = self.dequeue()
        if value is not None:
            self.enqueue(value)

    def to_list(self) -> list[T]:
        """Convertit la file en liste Python standard."""
        result: list[T] = []
        current = self._head
        while current is not None:
            result.append(current.value)
            current = current.next
        return result

    def __len__(self) -> int:
        """Retourne le nombre d'elements dans la file."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Iterateur pour parcourir la file."""
        current = self._head
        while current is not None:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        elements = [repr(item) for item in self]
        return f"Queue([{', '.join(elements)}])"


# ------------------------------------------------------------
# Structure de donnees: Table de Hachage avec Chainage (HashMap)
# ------------------------------------------------------------

@dataclass
class HashEntry(Generic[K, V]):
    """
    Entree d'une table de hachage (paire cle-valeur).

    Attributes:
        key: La cle de l'entree.
        value: La valeur associee a la cle.
    """
    key: K
    value: V


class HashMap(Generic[K, V]):
    """
    Structure de donnees: Table de Hachage (HashMap) avec Chainage

    Implementation d'un dictionnaire utilisant une table de hachage
    avec gestion des collisions par chainage (listes chainees).

    Chaque bucket contient une LinkedList d'entrees (HashEntry).
    Quand deux cles ont le meme hash, elles sont stockees dans
    la meme liste chainee.

    Complexite (cas moyen):
        - put: O(1)
        - get: O(1)
        - remove: O(1)
        - contains: O(1)

    Complexite (pire cas avec beaucoup de collisions):
        - Toutes operations: O(n)

    Attributes:
        _buckets: Tableau de listes chainees (buckets).
        _capacity: Nombre de buckets.
        _size: Nombre total d'entrees.
        _load_factor_threshold: Seuil pour le redimensionnement.
    """

    DEFAULT_CAPACITY = 16
    LOAD_FACTOR_THRESHOLD = 0.75

    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        """
        Initialise une table de hachage vide.

        Args:
            capacity: Nombre initial de buckets.
        """
        self._capacity = max(1, capacity)
        self._buckets: list[LinkedList[HashEntry[K, V]]] = [
            LinkedList() for _ in range(self._capacity)
        ]
        self._size = 0

    def _hash(self, key: K) -> int:
        """
        Calcule l'index du bucket pour une cle.

        Args:
            key: La cle a hacher.

        Returns:
            L'index du bucket (0 <= index < capacity).
        """
        return hash(key) % self._capacity

    def _resize(self) -> None:
        """
        Redimensionne la table quand le facteur de charge depasse le seuil.
        Double la capacite et rehache toutes les entrees.
        """
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [LinkedList() for _ in range(self._capacity)]
        self._size = 0

        for bucket in old_buckets:
            for entry in bucket:
                self.put(entry.key, entry.value)

    def put(self, key: K, value: V) -> None:
        """
        Insere ou met a jour une paire cle-valeur.

        Args:
            key: La cle.
            value: La valeur a associer.
        """
        # Verifier si redimensionnement necessaire
        if self._size / self._capacity > self.LOAD_FACTOR_THRESHOLD:
            self._resize()

        index = self._hash(key)
        bucket = self._buckets[index]

        # Chercher si la cle existe deja
        current = bucket.head
        while current is not None:
            if current.value.key == key:
                # Mise a jour de la valeur existante
                current.value.value = value
                return
            current = current.next

        # Nouvelle entree
        bucket.append(HashEntry(key, value))
        self._size += 1

    def get(self, key: K, default: V | None = None) -> V | None:
        """
        Recupere la valeur associee a une cle.

        Args:
            key: La cle a rechercher.
            default: Valeur par defaut si cle non trouvee.

        Returns:
            La valeur associee ou default si non trouvee.
        """
        index = self._hash(key)
        bucket = self._buckets[index]

        for entry in bucket:
            if entry.key == key:
                return entry.value

        return default

    def remove(self, key: K) -> bool:
        """
        Supprime une entree par sa cle.

        Args:
            key: La cle a supprimer.

        Returns:
            True si l'entree a ete trouvee et supprimee.
        """
        index = self._hash(key)
        bucket = self._buckets[index]

        # Trouver l'entree a supprimer
        current = bucket.head
        prev = None

        while current is not None:
            if current.value.key == key:
                if prev is None:
                    # Suppression de la tete
                    bucket._head = current.next
                else:
                    prev.next = current.next
                bucket._size -= 1
                self._size -= 1
                return True
            prev = current
            current = current.next

        return False

    def contains(self, key: K) -> bool:
        """
        Verifie si une cle existe dans la table.

        Args:
            key: La cle a rechercher.

        Returns:
            True si la cle existe.
        """
        return self.get(key) is not None

    def keys(self) -> list[K]:
        """Retourne toutes les cles de la table."""
        result: list[K] = []
        for bucket in self._buckets:
            for entry in bucket:
                result.append(entry.key)
        return result

    def values(self) -> list[V]:
        """Retourne toutes les valeurs de la table."""
        result: list[V] = []
        for bucket in self._buckets:
            for entry in bucket:
                result.append(entry.value)
        return result

    def items(self) -> list[tuple[K, V]]:
        """Retourne toutes les paires cle-valeur."""
        result: list[tuple[K, V]] = []
        for bucket in self._buckets:
            for entry in bucket:
                result.append((entry.key, entry.value))
        return result

    def setdefault(self, key: K, default: V) -> V:
        """
        Retourne la valeur de la cle si elle existe,
        sinon insere default et le retourne.

        Args:
            key: La cle a rechercher/inserer.
            default: Valeur par defaut a inserer si cle absente.

        Returns:
            La valeur existante ou default.
        """
        existing = self.get(key)
        if existing is not None:
            return existing
        self.put(key, default)
        return default

    def __len__(self) -> int:
        """Retourne le nombre d'entrees dans la table."""
        return self._size

    def __contains__(self, key: K) -> bool:
        """Verifie si une cle existe (operateur 'in')."""
        return self.contains(key)

    def __getitem__(self, key: K) -> V:
        """Acces par cle avec crochets (operateur [])."""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        """Affectation par cle avec crochets (operateur []=)."""
        self.put(key, value)

    def __iter__(self) -> Iterator[K]:
        """Iterateur sur les cles."""
        for bucket in self._buckets:
            for entry in bucket:
                yield entry.key

    def __repr__(self) -> str:
        items = [f"{k!r}: {v!r}" for k, v in self.items()]
        return f"HashMap({{{', '.join(items)}}})"


# ============================================================
# UTILITAIRES
# ============================================================

def _norm(s: str) -> str:
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


def _parse_datetime_any(x: object | None) -> datetime | None:
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


# ============================================================
# MODELES DE DOMAINE
# ============================================================

@dataclass
class Station:
    """
    Modele representant une station meteo.

    Attributes:
        id: Identifiant unique de la station.
        name: Nom affichable de la station.
        dataset_id: Identifiant du dataset ODS correspondant.
        meta: Metadonnees supplementaires.
    """
    id: str
    name: str
    dataset_id: str
    meta: JSONLike = field(default_factory=dict)


@dataclass
class WeatherRecord:
    """
    Modele representant une observation meteo.

    Attributes:
        station_id: ID de la station source.
        timestamp: Date/heure de l'observation.
        temperature_c: Temperature en degres Celsius.
        humidity_pct: Humidite relative en pourcentage.
        pressure_hpa: Pression atmospherique en hPa.
        wind_speed_ms: Vitesse du vent en m/s.
        wind_dir_deg: Direction du vent en degres.
        rain_mm: Precipitations en mm.
        raw: Donnees brutes originales.
    """
    station_id: str
    timestamp: datetime | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    wind_speed_ms: float | None = None
    wind_dir_deg: float | None = None
    rain_mm: float | None = None
    raw: JSONLike = field(default_factory=dict)


# ============================================================
# REPOSITORY (utilise HashMap)
# ============================================================

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


# ============================================================
# CLIENT HTTP ODS
# ============================================================

class ODSClient:
    """
    Client/Adapter Pattern: Abstraction de l'API Opendatasoft.

    Encapsule les appels HTTP vers l'API Explore v2.1 de Toulouse Metropole.

    Attributes:
        base_url: URL de base de l'API.
        session: Session HTTP persistante.
    """

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialise le client HTTP.

        Args:
            base_url: URL de base (utilise APP_CONFIG par defaut).
        """
        base = base_url or str(APP_CONFIG.get("base_url") or DEFAULT_BASE_URL)
        self.base_url = base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json; charset=utf-8",
            "User-Agent": "POO-Meteo/2.0 (+python requests)",
        })

    def _request(self, method: str, path: str, **kwargs) -> JSONLike:
        """Execute une requete HTTP."""
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, timeout=HTTP_TIMEOUT, **kwargs)
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            return resp.json()
        return {"_raw": resp.content}

    def catalog_datasets_page(
        self,
        limit: int = CATALOG_PAGE_SIZE,
        offset: int = 0,
        include_links: bool = False,
        include_app_metas: bool = False,
    ) -> JSONLike:
        """Recupere une page du catalogue de datasets."""
        params = {
            "limit": max(1, min(limit, CATALOG_PAGE_SIZE)),
            "offset": max(0, offset),
            "include_links": str(include_links).lower(),
            "include_app_metas": str(include_app_metas).lower(),
        }
        return self._request("GET", "/catalog/datasets", params=params)

    def catalog_datasets_iter(self, hard_limit: int | None = None) -> Iterator[JSONLike]:
        """Itere sur l'ensemble du catalogue."""
        catalog_cfg = APP_CONFIG.get("catalog") or {}
        default_limit = catalog_cfg.get("hard_limit", CATALOG_HARD_LIMIT)
        effective_hard_limit = hard_limit or int(default_limit)

        total_yielded = 0
        offset = 0
        while True:
            page = self.catalog_datasets_page(limit=CATALOG_PAGE_SIZE, offset=offset)
            results = page.get("results", []) or []
            if not results:
                break
            for ds in results:
                yield ds
                total_yielded += 1
                if total_yielded >= effective_hard_limit:
                    return
            offset += len(results)
            if offset >= (page.get("total_count") or 0):
                break

    def dataset_info(self, dataset_id: str) -> JSONLike:
        """Recupere les informations d'un dataset."""
        path = f"/catalog/datasets/{dataset_id}"
        return self._request("GET", path)

    def iter_records(
        self,
        dataset_id: str,
        select: str | None = None,
        where: str | None = None,
        order_by: str | None = None,
        limit: int = RECORDS_PAGE_SIZE,
        max_rows: int | None = None,
    ) -> Iterator[JSONLike]:
        """Itere sur les records d'un dataset."""
        params_base: dict[str, object] = {}
        if select:
            params_base["select"] = select
        if where:
            params_base["where"] = where
        if order_by:
            params_base["order_by"] = order_by

        yielded = 0
        offset = 0
        while True:
            remaining = (max_rows - yielded) if max_rows is not None else RECORDS_PAGE_SIZE
            page_limit = min(RECORDS_PAGE_SIZE, remaining) if max_rows is not None else RECORDS_PAGE_SIZE

            params = dict(params_base)
            params["limit"] = page_limit
            params["offset"] = offset

            res = self._request("GET", f"/catalog/datasets/{dataset_id}/records", params=params)
            results = res.get("results", []) or []
            if not results:
                break
            for row in results:
                yield row
                yielded += 1
                if max_rows is not None and yielded >= max_rows:
                    return
            offset += len(results)
            if len(results) < page_limit:
                break


# ============================================================
# NETTOYEUR DE DONNEES (Factory Pattern)
# ============================================================

class BasicCleaner:
    """
    Factory Pattern: Transforme les donnees brutes en objets WeatherRecord.

    Detecte les differents formats de champs meteo et normalise les donnees.
    """

    TEMP_KEYS = ["temperature", "temp", "temp_c", "tair", "temperature_c", "t", "tc"]
    HUM_KEYS = ["humidity", "humidite", "hum", "rh", "hr", "humidite_rel", "hum_rel"]
    P_KEYS = ["pressure", "pression", "press_hpa", "pression_hpa", "p", "pa", "p_hpa"]
    WIND_S_KEYS = ["wind_speed", "wind", "vitesse_vent", "ff", "ff10", "vent_ms", "vent_vitesse"]
    WIND_D_KEYS = ["wind_dir", "wind_direction", "dd", "dir_vent", "direction_vent"]
    RAIN_KEYS = ["rain", "pluie", "precipitation", "precipitations", "rr", "rr1", "rr24"]
    TS_PREF = ["date_observation", "date_mesure", "date_heure", "date", "datetime", "timestamp", "heure", "time"]

    def _get_first(self, data: JSONLike, keys: list[str]) -> object | None:
        """Cherche la premiere cle correspondante dans les donnees."""
        keys_norm = [_norm(k) for k in data.keys()]
        mapping = {kn: k for k, kn in zip(data.keys(), keys_norm)}
        for kk in keys:
            kkn = _norm(kk)
            if kkn in mapping:
                return data[mapping[kkn]]
        for kk in keys:
            kkn = _norm(kk)
            for kn, orig in mapping.items():
                if kkn in kn:
                    return data[orig]
        return None

    def _to_float(self, x: object | None) -> float | None:
        """Convertit une valeur en float."""
        if x is None or x == "":
            return None
        try:
            return float(str(x).replace(",", "."))
        except ValueError:
            return None

    def clean(self, raw: JSONLike, station_id: str) -> WeatherRecord:
        """
        Transforme des donnees brutes en WeatherRecord.

        Args:
            raw: Donnees brutes de l'API.
            station_id: ID de la station source.

        Returns:
            WeatherRecord normalise.
        """
        ts_raw = self._get_first(raw, self.TS_PREF)
        ts = _parse_datetime_any(ts_raw)

        t = self._to_float(self._get_first(raw, self.TEMP_KEYS))
        hum = self._to_float(self._get_first(raw, self.HUM_KEYS))
        p = self._to_float(self._get_first(raw, self.P_KEYS))
        ws = self._to_float(self._get_first(raw, self.WIND_S_KEYS))
        wd = self._to_float(self._get_first(raw, self.WIND_D_KEYS))
        rr = self._to_float(self._get_first(raw, self.RAIN_KEYS))

        return WeatherRecord(
            station_id=station_id,
            timestamp=ts,
            temperature_c=t,
            humidity_pct=hum,
            pressure_hpa=p,
            wind_speed_ms=ws,
            wind_dir_deg=wd,
            rain_mm=rr,
            raw=raw,
        )


# ============================================================
# CATALOGUE DE STATIONS (utilise LinkedList)
# ============================================================

class StationCatalogSimple:
    """
    Service de decouverte des stations meteo dans le catalogue.

    Utilise une LinkedList pour stocker les datasets detectes.

    Attributes:
        ods: Client HTTP ODS.
        repo: Repository pour stocker les stations.
        _weather: LinkedList des datasets meteo detectes.
    """

    TEMP_TOKENS = {
        "temperature", "temperatures", "temperature", "tair", "temp_c", "tc",
        "temp", "temperature_c",
    }
    HUM_TOKENS = {
        "humidity", "humidite", "humidite", "rh", "hr", "humidite_rel", "hum_rel",
    }
    PRESS_TOKENS = {
        "pression", "pressure", "press_hpa", "pression_hpa", "hpa",
    }
    WIND_TOKENS = {
        "vent", "wind", "rafale", "rafales", "gust", "ff", "ff10", "dd",
        "direction_vent", "vitesse_vent", "vent_ms",
    }
    RAIN_TOKENS = {
        "rain", "pluie", "pluvio", "precipitation", "precipitations", "rr",
        "rr1", "rr24", "rr24h",
    }

    EXCLUDE_DATASET_IDS = {
        "previsions-meteo-france-metropole",
    }

    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory) -> None:
        """
        Initialise le catalogue.

        Args:
            ods: Client HTTP ODS.
            repo: Repository pour stocker les stations.
        """
        self.ods = ods
        self.repo = repo
        self._weather: LinkedList[JSONLike] = LinkedList()

    def _is_weather_like(self, ds: JSONLike) -> bool:
        """Detecte si un dataset est une station meteo."""
        dsid = ds.get("dataset_id")
        if not dsid:
            return False

        if "station-meteo-" not in dsid:
            return False

        if dsid in self.EXCLUDE_DATASET_IDS:
            return False

        fields = ds.get("fields", []) or []
        fields_text = " ".join(
            f"{_norm(f.get('name') or '')} {_norm(f.get('label') or '')}"
            for f in fields
        )

        buf = []
        for ch in fields_text:
            if ch.isalnum():
                buf.append(ch)
            else:
                buf.append(" ")
        tokens = {tok for tok in "".join(buf).split() if tok}

        groups = 0
        if tokens & self.TEMP_TOKENS:
            groups += 1
        if tokens & self.HUM_TOKENS:
            groups += 1
        if tokens & self.PRESS_TOKENS:
            groups += 1
        if tokens & self.WIND_TOKENS:
            groups += 1
        if tokens & self.RAIN_TOKENS:
            groups += 1

        if groups == 0:
            return False

        has_geo = any((f.get("type") == "geo_point_2d") for f in fields)
        return (groups >= 2) or (groups >= 1 and has_geo)

    def load(self) -> None:
        """Charge le catalogue et detecte les stations meteo."""
        print("Chargement du catalogue (stations meteo Toulouse)...")

        for ds in self.ods.catalog_datasets_iter():
            if self._is_weather_like(ds):
                self._weather.append(ds)

        # Creation des stations dans le repository
        for ds in self._weather:
            metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
            title = metas.get("title") or ds.get("dataset_id")
            dsid = ds.get("dataset_id")
            if not dsid:
                continue
            st = Station(id=dsid, name=str(title), dataset_id=str(dsid), meta=metas)
            self.repo.upsert_station(st)

    def datasets(self) -> list[JSONLike]:
        """Retourne la liste des datasets meteo detectes."""
        return self._weather.to_list()


# ============================================================
# SERVICES METIER
# ============================================================

class WeatherIngestionService:
    """
    Service Layer Pattern: Ingestion des donnees meteo.

    Orchestre le chargement des donnees depuis l'API vers le repository.
    """

    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory, cleaner: BasicCleaner) -> None:
        self.ods = ods
        self.repo = repo
        self.cleaner = cleaner

    def _find_first_date_field(self, dataset_id: str) -> str | None:
        """Detecte le champ date principal d'un dataset."""
        info = self.ods.dataset_info(dataset_id)
        fields = (info.get("fields") or [])
        preferred = ["date_observation", "date_mesure", "date", "datetime", "timestamp", "time", "heure"]
        by_type = [f.get("name") for f in fields if f.get("type") in ("date", "datetime")]
        for p in preferred:
            if any(_norm(f.get("name") or "") == _norm(p) for f in fields):
                return p
        return by_type[0] if by_type else None

    def ingest_latest(self, station: Station, max_rows: int = 5) -> int:
        """Ingere les N dernieres observations d'une station."""
        dataset_id = station.dataset_id
        if not dataset_id:
            return 0

        order_field = None
        try:
            order_field = self._find_first_date_field(dataset_id)
        except requests.HTTPError:
            order_field = None

        order_by = f"{order_field} desc" if order_field else None
        count = 0
        try:
            for row in self.ods.iter_records(dataset_id=dataset_id, order_by=order_by, max_rows=max_rows):
                rec = self.cleaner.clean(row, station_id=station.id)
                self.repo.add_record(station.id, rec)
                count += 1
        except requests.HTTPError as e:
            print(f"Echec lecture records ({dataset_id}) : {e}")
        return count

    def ingest_all_latest(self, max_rows_per_station: int = 3, max_stations: int | None = None) -> int:
        """Ingere les observations pour toutes les stations."""
        stations = self.repo.list_stations()
        if max_stations is not None:
            stations = stations[:max_stations]

        total = 0
        for st in stations:
            n = self.ingest_latest(st, max_rows=max_rows_per_station)
            total += n
        return total


class WeatherQueryService:
    """Service Layer Pattern: Consultation des donnees meteo."""

    def __init__(self, repo: WeatherRepositoryMemory) -> None:
        self.repo = repo

    def latest_for_station(self, station_id: str, n: int = 1) -> list[WeatherRecord]:
        """Recupere les N dernieres observations d'une station."""
        return self.repo.latest_records(station_id, n=n)


class ForecastService:
    """
    Service Layer Pattern: Previsions meteo (jouet).

    Calcule une prevision simple basee sur la moyenne des dernieres observations.
    """

    def __init__(self, repo: WeatherRepositoryMemory) -> None:
        self.repo = repo

    def forecast_station_temp(self, station_id: str, last_n: int = 3) -> float | None:
        """
        Calcule une prevision de temperature.

        Args:
            station_id: ID de la station.
            last_n: Nombre d'observations a moyenner.

        Returns:
            Temperature prevue ou None si pas assez de donnees.
        """
        rows = self.repo.latest_records(station_id, n=last_n)
        temps = [r.temperature_c for r in rows if r.temperature_c is not None]
        if not temps:
            return None
        return sum(temps) / len(temps)


# ============================================================
# INTERFACE UTILISATEUR - RENDERERS
# ============================================================

class SimpleRenderer:
    """Strategy Pattern: Rendu console simple des donnees."""

    @staticmethod
    def print_datasets(datasets: list[JSONLike], max_rows: int = 20) -> None:
        """Affiche les datasets detectes."""
        print("\n=== Stations meteo detectees (Toulouse Metropole) ===")
        if not datasets:
            print("(aucune station meteo detectee)")
            return

        print(f"(affichage des {min(max_rows, len(datasets))} premiers sur {len(datasets)})\n")
        print(f"{'#':<4} {'dataset_id':<55} {'records':>7}  title")
        print("-" * PRINT_WIDTH)
        for i, ds in enumerate(datasets[:max_rows], 1):
            dsid = ds.get("dataset_id", "") or ""
            metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
            title = metas.get("title") or dsid
            records = metas.get("records_count")
            rec_s = f"{records}" if records is not None else "-"
            print(f"{i:<4} {dsid:<55} {rec_s:>7}  {str(title)[:40]}")
        print("-" * PRINT_WIDTH)

    @staticmethod
    def print_latest(repo: WeatherRepositoryMemory) -> None:
        """Affiche les dernieres observations."""
        print("\n=== Observations recentes par station ===")
        for st in repo.list_stations():
            latest = repo.latest_records(st.id, n=1)
            if latest:
                r = latest[0]
                ts = r.timestamp.isoformat(sep=" ", timespec="seconds") if r.timestamp else "-"
                t = f"{r.temperature_c:.1f}C" if r.temperature_c is not None else "?"
                hum = f"{r.humidity_pct:.0f}%" if r.humidity_pct is not None else "?"
                ws = f"{r.wind_speed_ms:.1f} m/s" if r.wind_speed_ms is not None else "?"
                rr = f"{r.rain_mm:.1f} mm" if r.rain_mm is not None else "0"
                print(f"[{st.dataset_id}] {st.name}")
                print(f"  -> {ts}  T={t}  H={hum}  Vent={ws}  Pluie={rr}")
            else:
                print(f"[{st.dataset_id}] {st.name}  •  derniere obs: -")

    @staticmethod
    def print_station_detail(station: Station, records: list[WeatherRecord], forecast: float | None) -> None:
        """Affiche le detail d'une station."""
        print("\n" + "=" * PRINT_WIDTH)
        print(f"  STATION: {station.name}")
        print(f"  ID: {station.dataset_id}")
        print("=" * PRINT_WIDTH)

        if not records:
            print("\n  Aucune observation disponible.")
        else:
            print("\n  Observations recentes:")
            print(f"  {'Date/Heure':<22} {'Temp':>8} {'Humid':>8} {'Vent':>10} {'Pluie':>8}")
            print("  " + "-" * 60)
            for r in records:
                ts = r.timestamp.strftime("%Y-%m-%d %H:%M") if r.timestamp else "-"
                t = f"{r.temperature_c:.1f}C" if r.temperature_c is not None else "-"
                hum = f"{r.humidity_pct:.0f}%" if r.humidity_pct is not None else "-"
                ws = f"{r.wind_speed_ms:.1f} m/s" if r.wind_speed_ms is not None else "-"
                rr = f"{r.rain_mm:.1f} mm" if r.rain_mm is not None else "-"
                print(f"  {ts:<22} {t:>8} {hum:>8} {ws:>10} {rr:>8}")

        print()
        if forecast is not None:
            print(f"  Prevision (moyenne): Temperature ~ {forecast:.1f}C")
        else:
            print("  Prevision: Donnees insuffisantes")
        print("=" * PRINT_WIDTH)


# ============================================================
# INTERFACE UTILISATEUR - CARROUSEL (utilise Queue)
# ============================================================

class StationCarouselRenderer:
    """
    Strategy Pattern: Carrousel cyclique des stations.

    Utilise une Queue pour gerer le parcours cyclique des stations.
    """

    def __init__(self, repo: WeatherRepositoryMemory, forecast: ForecastService, delay_seconds: int = 5) -> None:
        self.repo = repo
        self.forecast = forecast
        self.delay_seconds = delay_seconds
        self._queue: Queue[Station] = Queue()

    def _load_stations_to_queue(self) -> None:
        """Charge les stations dans la queue."""
        for st in self.repo.list_stations():
            self._queue.enqueue(st)

    def _format_record_line(self, st: Station) -> str:
        """Formate l'affichage d'une station."""
        latest = self.repo.latest_records(st.id, n=1)
        if not latest:
            return f"[{st.dataset_id}] {st.name}\n  Aucune observation recente disponible."
        r = latest[0]
        ts = r.timestamp.isoformat(sep=" ", timespec="seconds") if r.timestamp else "-"
        t = f"{r.temperature_c:.1f}C" if r.temperature_c is not None else "?"
        hum = f"{r.humidity_pct:.0f}%" if r.humidity_pct is not None else "?"
        ws = f"{r.wind_speed_ms:.1f} m/s" if r.wind_speed_ms is not None else "?"
        rr = f"{r.rain_mm:.1f} mm" if r.rain_mm is not None else "0"
        return (
            f"[{st.dataset_id}] {st.name}\n"
            f"  Derniere obs: {ts}\n"
            f"  T={t}  H={hum}  Vent={ws}  Pluie={rr}"
        )

    def _format_forecast_line(self, st: Station) -> str:
        """Formate la prevision d'une station."""
        yhat = self.forecast.forecast_station_temp(st.id)
        if yhat is None:
            return "  Prevision: indisponible (pas assez de donnees)"
        return f"  Prevision: temp ~ {yhat:.2f}C"

    def run(self) -> None:
        """Lance le carrousel cyclique."""
        self._load_stations_to_queue()

        if self._queue.is_empty():
            print("\nAucune station meteo detectee, rien a afficher.")
            return

        print("\n=== Carrousel des stations (Ctrl+C pour arreter) ===\n")

        try:
            while True:
                st = self._queue.peek()
                if st is None:
                    break

                print("=" * PRINT_WIDTH)
                print(self._format_record_line(st))
                print(self._format_forecast_line(st))
                print(f"\n-> Station suivante dans {self.delay_seconds} secondes...")

                time.sleep(self.delay_seconds)
                self._queue.rotate()

        except KeyboardInterrupt:
            print("\n\nArret du carrousel.")


# ============================================================
# INTERFACE UTILISATEUR - MENU INTERACTIF (Command Pattern)
# ============================================================

class StationSelectorMenu:
    """
    Command Pattern: Menu interactif de selection de station.

    Permet a l'utilisateur de:
    - Voir la liste des stations
    - Consulter une station specifique par numero
    - Rechercher une station par nom
    - Lancer le carrousel
    """

    def __init__(
        self,
        repo: WeatherRepositoryMemory,
        forecast: ForecastService,
        query: WeatherQueryService,
        carousel_delay: int = 5
    ) -> None:
        self.repo = repo
        self.forecast = forecast
        self.query = query
        self.carousel_delay = carousel_delay
        self._stations_list: list[Station] = []

    def _refresh_stations(self) -> None:
        """Met a jour la liste indexee des stations."""
        self._stations_list = self.repo.list_stations()

    def _print_header(self) -> None:
        """Affiche l'en-tete du menu."""
        print("\n" + "=" * PRINT_WIDTH)
        print("           METEO TOULOUSE METROPOLE - Menu Principal")
        print("=" * PRINT_WIDTH)

    def _print_stations_list(self) -> None:
        """Affiche la liste numerotee des stations."""
        print("\nStations disponibles:")
        print("-" * 70)
        for i, st in enumerate(self._stations_list, 1):
            name = st.name[:50] if len(st.name) > 50 else st.name
            print(f"  {i:3}. {name}")
        print("-" * 70)

    def _print_menu_options(self) -> None:
        """Affiche les options du menu."""
        print("\nActions:")
        print("  [1-N]  Consulter la station N")
        print("  [R]    Rechercher une station par nom")
        print("  [C]    Lancer le carrousel des stations")
        print("  [A]    Afficher toutes les observations recentes")
        print("  [Q]    Quitter")
        print()

    def _search_station(self, query: str) -> list[tuple[int, Station]]:
        """
        Recherche des stations par nom (recherche partielle).

        Args:
            query: Texte de recherche.

        Returns:
            Liste de tuples (index, Station) correspondants.
        """
        query_norm = _norm(query)
        results: list[tuple[int, Station]] = []

        for i, st in enumerate(self._stations_list, 1):
            name_norm = _norm(st.name)
            if query_norm in name_norm:
                results.append((i, st))

        return results

    def _show_station_detail(self, station: Station) -> None:
        """Affiche le detail d'une station."""
        records = self.query.latest_for_station(station.id, n=5)
        forecast_temp = self.forecast.forecast_station_temp(station.id)
        SimpleRenderer.print_station_detail(station, records, forecast_temp)

    def _handle_search(self) -> None:
        """Gere la recherche de station."""
        print("\nRecherche de station:")
        query = input("  Entrez le nom (ou partie du nom): ").strip()

        if not query:
            print("  Recherche annulee.")
            return

        results = self._search_station(query)

        if not results:
            print(f"  Aucune station trouvee pour '{query}'.")
            return

        if len(results) == 1:
            idx, station = results[0]
            print(f"  Station trouvee: {station.name}")
            self._show_station_detail(station)
        else:
            print(f"\n  {len(results)} station(s) trouvee(s):")
            for idx, st in results:
                print(f"    {idx}. {st.name}")

            choice = input("\n  Entrez le numero de la station (ou Entree pour annuler): ").strip()
            if choice.isdigit():
                num = int(choice)
                # Trouver la station correspondante
                for idx, st in results:
                    if idx == num:
                        self._show_station_detail(st)
                        return
                print("  Numero invalide.")

    def _handle_carousel(self) -> None:
        """Lance le carrousel."""
        carousel = StationCarouselRenderer(
            self.repo,
            self.forecast,
            delay_seconds=self.carousel_delay
        )
        carousel.run()

    def _handle_show_all(self) -> None:
        """Affiche toutes les observations recentes."""
        SimpleRenderer.print_latest(self.repo)

    def run(self) -> None:
        """Lance la boucle principale du menu."""
        self._refresh_stations()

        if not self._stations_list:
            print("\nAucune station meteo disponible.")
            print("Verifiez la connexion a l'API Toulouse Metropole.")
            return

        while True:
            self._print_header()
            self._print_stations_list()
            self._print_menu_options()

            choice = input("Votre choix: ").strip().upper()

            if choice == "Q":
                print("\nAu revoir!")
                break

            elif choice == "R":
                self._handle_search()
                input("\nAppuyez sur Entree pour continuer...")

            elif choice == "C":
                self._handle_carousel()
                input("\nAppuyez sur Entree pour continuer...")

            elif choice == "A":
                self._handle_show_all()
                input("\nAppuyez sur Entree pour continuer...")

            elif choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(self._stations_list):
                    station = self._stations_list[num - 1]
                    self._show_station_detail(station)
                    input("\nAppuyez sur Entree pour continuer...")
                else:
                    print(f"\nNumero invalide. Choisissez entre 1 et {len(self._stations_list)}.")
                    input("Appuyez sur Entree pour continuer...")

            else:
                print("\nOption non reconnue.")
                input("Appuyez sur Entree pour continuer...")


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def main() -> None:
    """
    Point d'entree principal de l'application.

    Workflow:
    1. Initialise les composants (client, repository, services)
    2. Charge le catalogue des stations meteo
    3. Ingere les observations recentes
    4. Lance le menu interactif
    """
    print("=" * PRINT_WIDTH)
    print("     APPLICATION METEO TOULOUSE METROPOLE")
    print("     Structures de donnees: LinkedList, Queue, HashMap")
    print("=" * PRINT_WIDTH)

    # Initialisation des composants
    ods = ODSClient()
    repo = WeatherRepositoryMemory()
    catalog = StationCatalogSimple(ods, repo)

    # Option: forcer un dataset via variable d'environnement
    force_id = os.environ.get("ODS_DATASET_ID")
    if force_id:
        print(f"\nMode station unique: {force_id}")
        st = Station(id=force_id, name=force_id, dataset_id=force_id)
        repo.upsert_station(st)
        ing = WeatherIngestionService(ods, repo, BasicCleaner())
        ing.ingest_latest(st, max_rows=10)

        fc = ForecastService(repo)
        query_svc = WeatherQueryService(repo)

        records = query_svc.latest_for_station(st.id, n=5)
        forecast_temp = fc.forecast_station_temp(st.id)
        SimpleRenderer.print_station_detail(st, records, forecast_temp)

        return

    # Chargement du catalogue
    try:
        catalog.load()
    except requests.HTTPError as e:
        print(f"Erreur lors du chargement du catalogue: {e}")
        sys.exit(1)

    ds_candidates = catalog.datasets()
    print(f"\n{len(ds_candidates)} stations meteo detectees.")

    if not ds_candidates:
        print("Aucune station meteo trouvee dans le catalogue.")
        sys.exit(0)

    # Ingestion des observations
    print("\nIngestion des observations recentes...")
    cleaner = BasicCleaner()
    ing = WeatherIngestionService(ods, repo, cleaner)

    ingestion_cfg = APP_CONFIG.get("ingestion") or {}
    max_rows_per_station = int(ingestion_cfg.get("max_rows_per_station", 5))
    max_stations_value = ingestion_cfg.get("max_stations")
    max_stations = int(max_stations_value) if isinstance(max_stations_value, int) else None

    total_rows = ing.ingest_all_latest(
        max_rows_per_station=max_rows_per_station,
        max_stations=max_stations,
    )
    print(f"Ingestion terminee: {total_rows} observations chargees.")

    # Services
    fc = ForecastService(repo)
    query_svc = WeatherQueryService(repo)

    # Lancement du menu interactif
    ui_cfg = APP_CONFIG.get("ui") or {}
    carousel_delay = int(ui_cfg.get("carousel_delay_sec", 5))

    menu = StationSelectorMenu(
        repo=repo,
        forecast=fc,
        query=query_svc,
        carousel_delay=carousel_delay
    )
    menu.run()


# ============================================================
# POINT D'ENTREE
# ============================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur.")
        sys.exit(0)
