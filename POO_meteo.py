# POO_meteo.py
# ------------------------------------------------------------
# Mini appli console pour découvrir l'API Opendatasoft (Explore v2.1)
# de Toulouse Métropole et ingérer des mesures météo.
#
# Points clés :
# - Client HTTP ODS propre avec pagination.
# - Recherche côté client (on évite where=search(...) source de 400).
# - Filtre strict "météo" par analyse des CHAMPS (temp, vent, pluie, etc.).
# - Ingestion triée par un vrai champ date/datetime, détecté automatiquement.
# - Possibilité de forcer un dataset via ODS_DATASET_ID.
# - Rendu console des datasets retenus + dernières observations.
#
# Python 3.12+
# ------------------------------------------------------------

from __future__ import annotations

import os
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
import requests

# ==============================
# Constantes
# ==============================

DEFAULT_BASE_URL = os.environ.get(
    "ODS_BASE_URL",
    "https://data.toulouse-metropole.fr/api/explore/v2.1"
)

HTTP_TIMEOUT = 20  # secondes
CATALOG_PAGE_SIZE = 100  # max autorisé sans group_by
CATALOG_HARD_LIMIT = 10_000  # sécurité
RECORDS_PAGE_SIZE = 100  # max autorisé pour records
PRINT_WIDTH = 110

JSONLike = dict[str, object]


# ==============================
# Helpers simples
# ==============================

def _norm(s: str) -> str:
    """Normalise texte : minuscule + suppression accents + trim."""
    if not isinstance(s, str):
        s = "" if s is None else str(s)
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


def _parse_datetime_any(x: object | None) -> datetime | None:
    """Tente de parser divers formats date/datetime retournés par ODS."""
    if x is None:
        return None
    if isinstance(x, datetime):
        return x
    s = str(x).strip()
    if not s:
        return None
    # Formats fréquents
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
    # Dernière chance : enlever le fuseau si présent
    if s.endswith("Z"):
        try:
            return datetime.strptime(s[:-1], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                return datetime.strptime(s[:-1], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                pass
    return None


# ==============================
# Domain models
# ==============================

@dataclass
class Station:
    id: str
    name: str
    dataset_id: str
    meta: JSONLike = field(default_factory=dict)


@dataclass
class WeatherRecord:
    station_id: str
    timestamp: datetime | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    wind_speed_ms: float | None = None
    wind_dir_deg: float | None = None
    rain_mm: float | None = None
    raw: JSONLike = field(default_factory=dict)


# ==============================
# Repositories en mémoire
# ==============================

class WeatherRepositoryMemory:
    def __init__(self) -> None:
        self._stations: dict[str, Station] = {}
        self._records: dict[str, list[WeatherRecord]] = {}

    def upsert_station(self, st: Station) -> None:
        self._stations[st.id] = st
        self._records.setdefault(st.id, [])

    def get_station(self, station_id: str) -> Station | None:
        return self._stations.get(station_id)

    def list_stations(self) -> list[Station]:
        return list(self._stations.values())

    def add_record(self, station_id: str, rec: WeatherRecord) -> None:
        self._records.setdefault(station_id, []).append(rec)

    def latest_records(self, station_id: str, n: int = 5) -> list[WeatherRecord]:
        arr = self._records.get(station_id, [])
        arr = sorted(arr, key=lambda r: r.timestamp or datetime.min, reverse=True)
        return arr[:n]


# ==============================
# Client ODS Explore v2.1
# ==============================

class ODSClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json; charset=utf-8",
            "User-Agent": "POO-Meteo/1.0 (+python requests)"
        })

    # --- HTTP core ---

    def _request(self, method: str, path: str, **kwargs) -> JSONLike:
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, timeout=HTTP_TIMEOUT, **kwargs)
        # Lève si 4xx/5xx pour permettre un try/except côté appelant
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("application/json"):
            return resp.json()
        # Pour endpoints exports renvoyant des fichiers, on pourrait gérer bytes ici
        return {"_raw": resp.content}

    # --- Catalog ---

    def catalog_datasets_page(
        self,
        limit: int = CATALOG_PAGE_SIZE,
        offset: int = 0,
        include_links: bool = False,
        include_app_metas: bool = False,
    ) -> JSONLike:
        params = {
            "limit": max(1, min(limit, CATALOG_PAGE_SIZE)),
            "offset": max(0, offset),
            "include_links": str(include_links).lower(),
            "include_app_metas": str(include_app_metas).lower(),
        }
        return self._request("GET", "/catalog/datasets", params=params)

    def catalog_datasets_iter(self, hard_limit: int = CATALOG_HARD_LIMIT) -> Iterator[JSONLike]:
        """Page sur l'ensemble du catalogue, sans 'where' côté serveur pour éviter les 400."""
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
                if total_yielded >= hard_limit:
                    return
            offset += len(results)
            # Sécurité anti-boucle
            if offset >= (page.get("total_count") or 0):
                break

    # --- Dataset info & records ---

    def dataset_info(self, dataset_id: str) -> JSONLike:
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
        """
        Itère sur les records du dataset.
        NB: /records a un maximum de 100 par page. On page manuellement si max_rows > 100.
        """
        params_base = {}
        if select:
            params_base["select"] = select
        if where:
            params_base["where"] = where
        if order_by:
            params_base["order_by"] = order_by

        yielded = 0
        offset = 0
        while True:
            params = dict(params_base)
            params["limit"] = min(RECORDS_PAGE_SIZE, (max_rows - yielded) if max_rows else RECORDS_PAGE_SIZE)
            params["offset"] = offset
            res = self._request("GET", f"/catalog/datasets/{dataset_id}/records", params=params)
            results = res.get("results", []) or []
            if not results:
                break
            for row in results:
                yield row
                yielded += 1
                if max_rows and yielded >= max_rows:
                    return
            offset += len(results)
            # Stop si on a moins que la page -> plus rien à lire
            if len(results) < params["limit"]:
                break


# ==============================
# Nettoyage / mapping champs
# ==============================

class BasicCleaner:
    """
    Transforme une ligne brute ODS en WeatherRecord.
    Détecte au mieux les synonymes de champs (température, humidité, etc.)
    """

    TEMP_KEYS = ["temperature", "temp", "temp_c", "tair", "temperature_c", "t", "tc"]
    HUM_KEYS = ["humidity", "humidite", "hum", "rh", "hr", "humidite_rel", "hum_rel"]
    P_KEYS = ["pressure", "pression", "press_hpa", "pression_hpa", "p", "pa", "p_hpa"]
    WIND_S_KEYS = ["wind_speed", "wind", "vitesse_vent", "ff", "ff10", "vent_ms", "vent_vitesse"]
    WIND_D_KEYS = ["wind_dir", "wind_direction", "dd", "dir_vent", "direction_vent"]
    RAIN_KEYS = ["rain", "pluie", "precipitation", "precipitations", "rr", "rr1", "rr24"]

    TS_PREF = ["date_observation", "date_mesure", "date_heure", "date", "datetime", "timestamp", "heure", "time"]

    def _get_first(self, data: JSONLike, keys: list[str]) -> object | None:
        keys_norm = [_norm(k) for k in data.keys()]
        mapping = {kn: k for k, kn in zip(data.keys(), keys_norm)}
        for kk in keys:
            kkn = _norm(kk)
            if kkn in mapping:
                return data[mapping[kkn]]
        # fallback: recherche partielle
        for kk in keys:
            kkn = _norm(kk)
            for kn, orig in mapping.items():
                if kkn in kn:
                    return data[orig]
        return None

    def _to_float(self, x: object | None) -> float | None:
        if x is None or x == "":
            return None
        try:
            return float(str(x).replace(",", "."))
        except ValueError:
            return None

    def clean(self, raw: JSONLike, station_id: str) -> WeatherRecord:
        # Timestamp
        ts_raw = self._get_first(raw, self.TS_PREF)
        ts = _parse_datetime_any(ts_raw)

        # Mesures
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
            raw=raw
        )


# ==============================
# Catalogue de stations (détection datasets météo)
# ==============================

class StationCatalogSimple:
    """
    Explore le catalogue et identifie des datasets 'météo' plausibles
    en analysant les CHAMPS (noms + labels) — pas les métadonnées globales.
    """

    FIELD_KEYWORDS = [
        # Température
        "temperature", "température", "tair", "temp_c", "tc",
        # Humidité
        "humidity", "humidité", "rh", "hr",
        # Pression
        "pression", "pressure", "hpa",
        # Vent
        "vent", "wind", "rafale", "gust", "ff", "dd",
        # Pluie
        "pluie", "rain", "precipitation", "précipitation", "rr",
        # Rayonnement / UV / soleil (bonus)
        "uv", "ensoleil", "rayonnement", "solar"
    ]
    EXCLUDE_THEMES = {"finance", "citoyennete", "culture", "education", "mobilite", "transport"}

    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory) -> None:
        self.ods = ods
        self.repo = repo
        self._weather: list[JSONLike] = []

    def _is_weather_like(self, ds: JSONLike) -> bool:
        fields = ds.get("fields", []) or []
        fields_text = " ".join(
            f"{_norm(f.get('name') or '')} {_norm(f.get('label') or '')}"
            for f in fields
        )
        has_measure = any(k in fields_text for k in self.FIELD_KEYWORDS)
        if not has_measure:
            return False

        metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
        themes = [_norm(t) for t in (metas.get("theme") or [])]
        if any(t in self.EXCLUDE_THEMES for t in themes):
            # Certains datasets météo peuvent être rangés ailleurs : on est souple.
            pass

        # Bonus : présence d'un champ géo (fréquent pour capteurs)
        has_geo = any((f.get("type") == "geo_point_2d") for f in fields)
        return has_measure or has_geo

    def load(self) -> None:
        print("Chargement du catalogue (détection datasets météo)…")
        # Pas de 'where' côté serveur -> pagination full + filtre local
        items: list[JSONLike] = []
        for ds in self.ods.catalog_datasets_iter(hard_limit=CATALOG_HARD_LIMIT):
            if self._is_weather_like(ds):
                items.append(ds)
        self._weather = items

        # Création de "stations" à partir des datasets retenus
        for ds in self._weather:
            metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
            title = metas.get("title") or ds.get("dataset_id")
            dsid = ds.get("dataset_id")
            if not dsid:
                continue
            st = Station(id=dsid, name=title, dataset_id=dsid, meta=metas)
            self.repo.upsert_station(st)

    def datasets(self) -> list[JSONLike]:
        return list(self._weather)


# ==============================
# Services
# ==============================

class WeatherIngestionService:
    def __init__(self, ods: ODSClient, repo: WeatherRepositoryMemory, cleaner: BasicCleaner) -> None:
        self.ods = ods
        self.repo = repo
        self.cleaner = cleaner

    def _find_first_date_field(self, dataset_id: str) -> str | None:
        info = self.ods.dataset_info(dataset_id)
        fields = (info.get("fields") or [])
        # priorité aux champs nommés logiquement
        preferred = ["date_observation", "date_mesure", "date", "datetime", "timestamp", "time", "heure"]
        by_type = [f.get("name") for f in fields if f.get("type") in ("date", "datetime")]
        # D'abord "preferred" si présent, sinon premier champ date
        for p in preferred:
            if any(_norm(f.get("name") or "") == _norm(p) for f in fields):
                return p
        return by_type[0] if by_type else None

    def ingest_latest(self, station: Station, max_rows: int = 5) -> int:
        """Ingestion des N dernières lignes d'un dataset trié par date décroissante si possible."""
        dataset_id = station.dataset_id
        if not dataset_id:
            return 0

        order_field = None
        try:
            order_field = self._find_first_date_field(dataset_id)
        except requests.HTTPError:
            # On tentera sans tri explicite
            order_field = None

        order_by = f"{order_field} desc" if order_field else None
        count = 0
        try:
            for row in self.ods.iter_records(dataset_id=dataset_id, order_by=order_by, max_rows=max_rows):
                rec = self.cleaner.clean(row, station_id=station.id)
                self.repo.add_record(station.id, rec)
                count += 1
        except requests.HTTPError as e:
            print(f"Échec lecture records ({dataset_id}) : {e}")
        return count

    def ingest_all_latest(self, max_rows_per_station: int = 3, max_stations: int = 5) -> int:
        total = 0
        for st in self.repo.list_stations()[:max_stations]:
            n = self.ingest_latest(st, max_rows=max_rows_per_station)
            total += n
        return total


class WeatherQueryService:
    def __init__(self, repo: WeatherRepositoryMemory) -> None:
        self.repo = repo

    def latest_for_station(self, station_id: str, n: int = 1) -> list[WeatherRecord]:
        return self.repo.latest_records(station_id, n=n)


class ForecastService:
    """Prévision jouet = moyenne des 3 dernières températures observées."""
    def __init__(self, repo: WeatherRepositoryMemory) -> None:
        self.repo = repo

    def forecast_station_temp(self, station_id: str, last_n: int = 3) -> float | None:
        rows = self.repo.latest_records(station_id, n=last_n)
        temps = [r.temperature_c for r in rows if r.temperature_c is not None]
        if not temps:
            return None
        return sum(temps) / len(temps)


# ==============================
# Rendu console
# ==============================

class SimpleRenderer:
    @staticmethod
    def print_datasets(datasets: list[JSONLike], max_rows: int = 20) -> None:
        print("\n=== Candidats 'météo' détectés dans le catalogue ===")
        if not datasets:
            print("(aucun dataset météo détecté via analyse des champs)")
            return

        print(f"(affichage des {min(max_rows, len(datasets))} premiers sur {len(datasets)})\n")
        print(f"{'dataset_id':<60} {'records':>7}  title")
        print("-" * PRINT_WIDTH)
        for ds in datasets[:max_rows]:
            dsid = ds.get("dataset_id", "") or ""
            metas = (ds.get("metas", {}) or {}).get("default", {}) or {}
            title = metas.get("title") or dsid
            records = metas.get("records_count")
            rec_s = f"{records}" if records is not None else "-"
            print(f"{dsid:<60} {rec_s:>7}  {title[:PRINT_WIDTH-80]}")
        print("-" * PRINT_WIDTH)

    @staticmethod
    def print_latest(repo: WeatherRepositoryMemory, max_rows: int = 5) -> None:
        print("\n=== Observations récentes par 'station' ===")
        for st in repo.list_stations():
            latest = repo.latest_records(st.id, n=1)
            if latest:
                r = latest[0]
                ts = r.timestamp.isoformat(sep=" ", timespec="seconds") if r.timestamp else "-"
                t = f"{r.temperature_c:.1f}°C" if r.temperature_c is not None else "?"
                hum = f"{r.humidity_pct:.0f}%" if r.humidity_pct is not None else "?"
                ws = f"{r.wind_speed_ms:.1f} m/s" if r.wind_speed_ms is not None else "?"
                rr = f"{r.rain_mm:.1f} mm" if r.rain_mm is not None else "0"
                print(f"[{st.dataset_id}] {st.name}  •  dernière obs: {ts}  •  T={t}  H={hum}  Vent={ws}  Pluie={rr}")
            else:
                print(f"[{st.dataset_id}] {st.name}  •  dernière obs: -")


# ==============================
# Main
# ==============================

def main() -> None:
    ods = ODSClient(base_url=DEFAULT_BASE_URL)
    repo = WeatherRepositoryMemory()
    catalog = StationCatalogSimple(ods, repo)

    # Option : forcer un dataset précis via variable d'environnement
    force_id = os.environ.get("ODS_DATASET_ID")
    if force_id:
        print(f"Ingestion forcée du dataset: {force_id}")
        st = Station(id=force_id, name=force_id, dataset_id=force_id)
        repo.upsert_station(st)
        ing = WeatherIngestionService(ods, repo, BasicCleaner())
        ing.ingest_latest(st, max_rows=10)
        SimpleRenderer.print_latest(repo, max_rows=1)

        # Petite prévision jouet
        fc = ForecastService(repo)
        yhat = fc.forecast_station_temp(st.id)
        if yhat is not None:
            print(f"\nPrévision jouet pour {st.name} → temp ≈ {yhat:.2f} °C")
        return

    # Parcours du catalogue + détection datasets météo (filtre strict par champs)
    try:
        catalog.load()
    except requests.HTTPError as e:
        print("Erreur en chargeant le catalogue:", e)
        raise

    ds_candidates = catalog.datasets()
    SimpleRenderer.print_datasets(ds_candidates, max_rows=20)

    # Ingestion d'un petit échantillon pour quelques stations
    cleaner = BasicCleaner()
    ing = WeatherIngestionService(ods, repo, cleaner)
    ing.ingest_all_latest(max_rows_per_station=3, max_stations=5)

    # Rendu des dernières mesures
    SimpleRenderer.print_latest(repo, max_rows=5)

    # Prévision jouet sur quelques stations
    fc = ForecastService(repo)
    for st in repo.list_stations()[:3]:
        yhat = fc.forecast_station_temp(st.id)
        if yhat is not None:
            print(f"Prévision jouet pour {st.name} → temp ≈ {yhat:.2f} °C")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
