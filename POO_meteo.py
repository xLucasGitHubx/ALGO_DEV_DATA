# POO_meteo.py
# ---------------------------------------
# Petit framework "météo" + client Opendatasoft (ODS)
# Domaine: https://data.toulouse-metropole.fr (modifiable via ENV/const)
#
# Fonctionnement principal du "catalogue":
# - On ne fait PLUS de where=search() sur /catalog/datasets (ça 400 parfois)
# - On pagine le catalogue (limit=100) puis on filtre en Python (sans accents)
#
# Exécution:
#   python POO_meteo.py
#
# ---------------------------------------

from __future__ import annotations

import os
import json
import math
import time
import unicodedata
import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

import requests


# ==========================
# Config
# ==========================

DEFAULT_BASE_URL = os.environ.get(
    "ODS_BASE_URL",
    "https://data.toulouse-metropole.fr",
)

HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "30"))  # seconds
CATALOG_PAGE_LIMIT = 100          # pagination size for catalog
CATALOG_HARD_LIMIT = 2000         # safety bound when fetching all datasets
RECORDS_PAGE_LIMIT = 100          # pagination size for dataset records


# ==========================
# Helpers
# ==========================

def _norm(s: str) -> str:
    """
    Normalise une chaîne pour recherche tolérante:
    - str() + lower()
    - NFKD + suppression des accents
    - retourne "" si None
    """
    if s is None:
        return ""
    s = str(s).lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        # gère "2025-01-02T03:04:05+00:00" ou "2025-01-02"
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ==========================
# ODS Client
# ==========================

class ODSClient:
    """
    Client minimal Opendatasoft Explore v2.1
    Docs interactives: {base}/api/explore/v2.1
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        # Petite UA propre pour le domaine
        self.session.headers.update({
            "User-Agent": "POO-Meteo/1.0 (+LucasM; script demo)",
            "Accept": "application/json; charset=utf-8",
        })

    # -------- Catalogue (datasets) --------

    def _catalog_search(self, query: Optional[str], hard_limit: int = CATALOG_HARD_LIMIT) -> List[Dict[str, Any]]:
        """
        ⚠️ Ne PAS utiliser where=search() côté catalog → certains domaines renvoient 400.
        On récupère tout le catalogue par pages (limit<=100) puis on filtre en Python.
        """
        url = f"{self.base_url}/api/explore/v2.1/catalog/datasets"

        offset = 0
        out: List[Dict[str, Any]] = []

        while True:
            params = {
                "limit": CATALOG_PAGE_LIMIT,
                "offset": offset,
                "include_links": "false",
                "include_app_metas": "false",
            }
            r = self.session.get(url, params=params, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            js = r.json()
            results = js.get("results", [])
            out.extend(results)

            total = int(js.get("total_count", 0))
            offset += CATALOG_PAGE_LIMIT
            if offset >= total or len(out) >= hard_limit:
                break

        # Filtrage local si query fournie
        if query:
            qn = _norm(query)
            filtered: List[Dict[str, Any]] = []
            for ds in out:
                blob = _norm(json.dumps(ds, ensure_ascii=False))
                if qn in blob:
                    filtered.append(ds)
            return filtered[:hard_limit]

        return out[:hard_limit]

    def find_weather_datasets(self) -> List[Dict[str, Any]]:
        """
        Cherche des datasets "météo" en récupérant d'abord le catalogue complet,
        puis en filtrant localement sur des mots-clés (sans accents).
        """
        terms = [
            "meteo", "météo", "temperature", "température",
            "pluie", "precip", "précip", "vent", "rafale",
            "station meteo", "capteur", "humid", "pression",
            "uv", "ensoleil", "neige"
        ]
        all_ds = self._catalog_search(query=None, hard_limit=CATALOG_HARD_LIMIT)

        seen: Dict[str, Dict[str, Any]] = {}
        for ds in all_ds:
            did = ds.get("dataset_id")
            if not did or did in seen:
                continue

            blob = _norm(json.dumps(ds, ensure_ascii=False))
            if any(_norm(t) in blob for t in terms):
                # On garde si présence de champs météo potentiels
                fields = [f.get("name", "").lower() for f in ds.get("fields", [])]
                if any(k in blob for k in (
                    "meteo", "temperature", "temp", "pluie", "precip", "vent",
                    "humidity", "humidit", "pression", "pressure", "rafale", "gust"
                )):
                    seen[did] = ds

        return list(seen.values())

    # -------- Dataset info & records --------

    def dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}"
        r = self.session.get(url, timeout=HTTP_TIMEOUT, params={"include_links": "false", "include_app_metas": "false"})
        r.raise_for_status()
        return r.json()

    def iter_records(
        self,
        dataset_id: str,
        select: Optional[str] = None,
        where: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: int = RECORDS_PAGE_LIMIT,
        max_rows: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Itère sur les enregistrements du dataset (pagination côté API).
        - Contrairement au CATALOG, on peut utiliser where/order_by ici sans souci.
        """
        url = f"{self.base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
        offset = 0
        yielded = 0

        while True:
            params: Dict[str, Any] = {
                "limit": limit,
                "offset": offset,
            }
            if select:
                params["select"] = select
            if where:
                params["where"] = where
            if order_by:
                params["order_by"] = order_by

            r = self.session.get(url, timeout=HTTP_TIMEOUT, params=params)
            r.raise_for_status()
            js = r.json()
            results = js.get("results", [])
            if not results:
                break

            for row in results:
                yield row
                yielded += 1
                if max_rows is not None and yielded >= max_rows:
                    return

            total = int(js.get("total_count", 0))
            offset += limit
            if offset >= total:
                break


# ==========================
# Domain model
# ==========================

@dataclass
class Station:
    id: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    dataset_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WeatherRecord:
    ts: Optional[datetime]
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_ms: Optional[float] = None
    rainfall_mm: Optional[float] = None
    station_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WeatherSeries:
    station: Station
    records: List[WeatherRecord] = field(default_factory=list)

    def latest(self) -> Optional[WeatherRecord]:
        if not self.records:
            return None
        # Suppose ts peut être None -> trie en plaçant None en bas
        return sorted(self.records, key=lambda r: (r.ts is None, r.ts))[-1]

    def __len__(self) -> int:
        return len(self.records)


# ==========================
# Cleaner / Mapper
# ==========================

class BasicCleaner:
    """
    Convertit un enregistrement brut (dict ODS) en WeatherRecord
    en essayant plusieurs alias de champs.
    """
    TEMP_KEYS = ["temperature", "temp_c", "temp", "tair", "temperature_c", "temperatures", "t"]
    HUM_KEYS = ["humidity", "humidite", "humidite_%", "humidite_relative", "rh", "humi", "humidity_pct"]
    PRES_KEYS = ["pression", "pression_hpa", "pressure", "p", "press"]
    WIND_KEYS = ["wind", "wind_speed", "vitesse_vent", "vent_ms", "vent", "ffraf", "ff"]
    RAIN_KEYS = ["rain", "pluie", "precip", "precip_mm", "rr", "pluie_mm"]

    TS_KEYS = ["timestamp", "date_heure", "datetime", "time", "date", "obs_time", "measurement_time"]

    def get_first(self, d: Dict[str, Any], keys: List[str]) -> Optional[Any]:
        for k in keys:
            if k in d:
                return d.get(k)
        # tente sans accents et minuscules
        nd = { _norm(k): v for k, v in d.items() }
        for k in keys:
            if _norm(k) in nd:
                return nd.get(_norm(k))
        return None

    def to_float(self, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except Exception:
            # parfois "12,3"
            try:
                return float(str(v).replace(",", "."))
            except Exception:
                return None

    def to_dt(self, v: Any) -> Optional[datetime]:
        if isinstance(v, datetime):
            return v
        if v is None:
            return None
        if isinstance(v, (int, float)) and v > 1e11:  # ms epoch?
            try:
                return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
            except Exception:
                pass
        return _parse_dt(str(v))

    def clean(self, raw: Dict[str, Any], station_id: Optional[str] = None) -> WeatherRecord:
        # Les lignes ODS ont souvent ce format:
        # {"field1": "...", ..., "geo_point_2d": {"lat": ..., "lon": ...}, "recordid": "..."}
        # On travaille sur une "couche" qui peut être incluse (parfois, enregistrements imbriqués)
        flat = dict(raw)
        # certains datasets mettent la _source ou "fields" -> harmonisation légère
        src = flat.get("fields") if isinstance(flat.get("fields"), dict) else None
        if src:
            for k, v in src.items():
                flat.setdefault(k, v)

        ts = self.to_dt(self.get_first(flat, self.TS_KEYS))
        temp = self.to_float(self.get_first(flat, self.TEMP_KEYS))
        hum = self.to_float(self.get_first(flat, self.HUM_KEYS))
        pres = self.to_float(self.get_first(flat, self.PRES_KEYS))
        wind = self.to_float(self.get_first(flat, self.WIND_KEYS))
        rain = self.to_float(self.get_first(flat, self.RAIN_KEYS))

        return WeatherRecord(
            ts=ts,
            temperature_c=temp,
            humidity_pct=hum,
            pressure_hpa=pres,
            wind_ms=wind,
            rainfall_mm=rain,
            station_id=station_id,
            raw=raw,
        )


# ==========================
# Repository (mémoire)
# ==========================

class WeatherRepositoryMemory:
    def __init__(self):
        self.stations: Dict[str, Station] = {}
        self.series_by_station: Dict[str, WeatherSeries] = {}

    def upsert_station(self, st: Station) -> None:
        self.stations[st.id] = st
        self.series_by_station.setdefault(st.id, WeatherSeries(station=st))

    def add_record(self, station_id: str, rec: WeatherRecord) -> None:
        if station_id not in self.series_by_station:
            raise KeyError(f"Station inconnue: {station_id}")
        self.series_by_station[station_id].records.append(rec)

    def get_series(self, station_id: str) -> Optional[WeatherSeries]:
        return self.series_by_station.get(station_id)

    def list_stations(self) -> List[Station]:
        return list(self.stations.values())


# ==========================
# Catalogue Stations (démo)
# ==========================

class StationCatalogSimple:
    """
    Pour la démo: on ne "résout" pas de vraies stations physiques.
    On détecte des datasets météo candidats et on crée une pseudo-ligne par dataset.
    """

    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory):
        self.ods = ods
        self.repo = repo
        self._datasets: List[Dict[str, Any]] = []

    def load(self) -> None:
        print("Chargement du catalogue (détection datasets météo)…")
        self._datasets = self.ods.find_weather_datasets()
        # On matérialise une "Station" par dataset pour l’exemple
        for ds in self._datasets:
            did = ds.get("dataset_id", "unknown-id")
            title = (ds.get("metas", {}) or {}).get("default", {}).get("title") or did
            # lat/lon non garanties au niveau dataset → None
            st = Station(id=did, name=title, lat=None, lon=None, dataset_id=did, raw=ds)
            self.repo.upsert_station(st)

    def datasets(self) -> List[Dict[str, Any]]:
        return self._datasets


# ==========================
# Renderer (console)
# ==========================

class SimpleRenderer:
    @staticmethod
    def print_datasets(ds_list: List[Dict[str, Any]], max_rows: int = 20) -> None:
        print("")
        print("=== Candidats 'météo' détectés dans le catalogue ===")
        if not ds_list:
            print("(aucun)")
            return
        print(f"(affichage des {min(max_rows, len(ds_list))} premiers sur {len(ds_list)})")
        print("")
        print(f"{'dataset_id':<60}  {'records':>8}  title")
        print("-" * 110)
        for i, ds in enumerate(ds_list[:max_rows]):
            did = ds.get("dataset_id", "-")
            metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
            title = metas.get("title") or "-"
            records = metas.get("records_count")
            if records is None:
                # parfois "has_records": bool
                records = "?"
            print(f"{did:<60}  {str(records):>8}  {title}")
        print("-" * 110)

    @staticmethod
    def print_latest(repo: WeatherRepositoryMemory, max_rows: int = 10) -> None:
        print("")
        print("=== Observations récentes par 'station' (demo) ===")
        stations = repo.list_stations()[:max_rows]
        for st in stations:
            series = repo.get_series(st.id)
            last = series.latest() if series else None
            if last and last.ts:
                ts = last.ts.isoformat()
            else:
                ts = "-"
            print(f"[{st.id}] {st.name}  •  dernière obs: {ts}")


# ==========================
# Services (ingestion, requêtes, forecast)
# ==========================

class WeatherIngestionService:
    """
    Démo ingestion: pour chaque "station" (ici = dataset),
    on tente de lire des enregistrements triés récents.
    """
    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory, cleaner: BasicCleaner):
        self.ods = ods
        self.repo = repo
        self.cleaner = cleaner

    def ingest_latest(self, station: Station, max_rows: int = 5) -> int:
        dataset_id = station.dataset_id
        if not dataset_id:
            return 0

        count = 0
        try:
            for row in self.ods.iter_records(
                dataset_id=dataset_id,
                order_by="date desc"  # si le champ existe; sinon l'API ignore
            ):
                rec = self.cleaner.clean(row, station_id=station.id)
                self.repo.add_record(station.id, rec)
                count += 1
                if count >= max_rows:
                    break
        except requests.HTTPError as e:
            # datasets hétérogènes → certains n'ont pas de /records exploitable
            # on ignore silencieusement pour la démo
            pass
        return count

    def ingest_all_latest(self, max_rows_per_station: int = 5, max_stations: int = 10) -> None:
        stations = self.repo.list_stations()[:max_stations]
        for st in stations:
            _ = self.ingest_latest(st, max_rows=max_rows_per_station)


class WeatherQueryService:
    def __init__(self, repo: WeatherRepositoryMemory):
        self.repo = repo

    def latest_for_station(self, station_id: str) -> Optional[WeatherRecord]:
        series = self.repo.get_series(station_id)
        return series.latest() if series else None


class SimpleForecaster:
    """
    Mini "prévision" jouet (moyenne glissante précédente).
    """
    def forecast_next_temp(self, series: WeatherSeries, window: int = 3) -> Optional[float]:
        vals: List[float] = [r.temperature_c for r in series.records if r.temperature_c is not None]
        if len(vals) == 0:
            return None
        if len(vals) <= window:
            return sum(vals) / len(vals)
        return sum(vals[-window:]) / window


class ForecastService:
    def __init__(self, repo: WeatherRepositoryMemory):
        self.repo = repo
        self.model = SimpleForecaster()

    def forecast_station_temp(self, station_id: str, window: int = 3) -> Optional[float]:
        series = self.repo.get_series(station_id)
        if not series:
            return None
        return self.model.forecast_next_temp(series, window=window)


# ==========================
# CLI
# ==========================

def main() -> None:
    ods = ODSClient(base_url=DEFAULT_BASE_URL)
    repo = WeatherRepositoryMemory()
    catalog = StationCatalogSimple(ods, repo)

    try:
        catalog.load()
    except requests.HTTPError as e:
        print("Erreur en chargeant le catalogue:", e)
        raise

    ds_candidates = catalog.datasets()
    SimpleRenderer.print_datasets(ds_candidates, max_rows=20)

    # Ingestion démo sur quelques datasets → juste pour montrer que ça tourne
    cleaner = BasicCleaner()
    ing = WeatherIngestionService(ods, repo, cleaner)
    ing.ingest_all_latest(max_rows_per_station=3, max_stations=5)

    # Affichage dernières obs (si dispo)
    SimpleRenderer.print_latest(repo, max_rows=5)

    # Démo forecast "moyenne" si on a des valeurs
    fc = ForecastService(repo)
    for st in repo.list_stations()[:3]:
        yhat = fc.forecast_station_temp(st.id)
        if yhat is not None:
            print(f"Prévision jouet pour {st.name} → temp ≈ {yhat:.2f} °C")


if __name__ == "__main__":
    main()
