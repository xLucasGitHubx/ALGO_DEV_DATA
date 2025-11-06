"""
Toulouse Météo — OOP, SOLID, Clean Code (API only)
=================================================

Run:
  pip install -r requirements.txt
  python app.py --metro "Capitole" --hours 24 --forecast 6 --profile

requirements.txt (minimal)
  requests
  pandas
  numpy
  ydata-profiling    # optional
  ydata-sdk          # optional

Notes:
- API only (no CSV) via Opendatasoft Explore v2.1.
- Prefer Europe/Paris timezone.
- If ydata-sdk is available, extended quality scoring/outliers/redundancy checks are attempted; else fallback.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

try:
    from ydata_profiling import ProfileReport  # type: ignore
    _HAS_PROFILING = True
except Exception:
    _HAS_PROFILING = False

try:
    import ydata_sdk  # type: ignore
    _HAS_YDATA_SDK = True
except Exception:
    _HAS_YDATA_SDK = False


@dataclass(frozen=True)
class StationId:
    value: str


@dataclass(frozen=True)
class StationLigne:
    code: Optional[str] = None
    name: Optional[str] = None


@dataclass
class Station:
    id: StationId
    name: str
    latitude: float
    longitude: float
    kind: str
    ligne: Optional[StationLigne] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WeatherRecord:
    station_id: StationId
    timestamp: dt.datetime
    temperature_c: Optional[float]
    humidity_pct: Optional[float]
    pressure_hpa: Optional[float]


@dataclass
class WeatherSeries:
    station: Station
    records: List[WeatherRecord]


class IDataSource(ABC):
    @abstractmethod
    def fetch_weather_station_catalog(self) -> List[Station]:
        ...

    @abstractmethod
    def fetch_metro_station_catalog(self) -> List[Station]:
        ...

    @abstractmethod
    def fetch_weather_records(
        self,
        dataset_id: str,
        since: Optional[dt.datetime] = None,
        until: Optional[dt.datetime] = None,
        limit: int = 10_000,
    ) -> pd.DataFrame:
        ...


class ICleaner(ABC):
    @abstractmethod
    def clean_weather_df(self, df: pd.DataFrame, station_id: StationId) -> pd.DataFrame:
        ...


class IForecaster(ABC):
    @abstractmethod
    def forecast(self, df: pd.DataFrame, horizon_hours: int, freq: str = "1H") -> pd.DataFrame:
        ...


class IRepository(ABC):
    @abstractmethod
    def save_series(self, series: WeatherSeries) -> None:
        ...

    @abstractmethod
    def get_series(
        self,
        station_id: StationId,
        since: Optional[dt.datetime] = None,
        until: Optional[dt.datetime] = None,
    ) -> pd.DataFrame:
        ...


class IRenderer(ABC):
    @abstractmethod
    def show_current(self, df: pd.DataFrame) -> None:
        ...

    @abstractmethod
    def show_forecast(self, df_fc: pd.DataFrame) -> None:
        ...


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class OpendatasoftAPIDataSource(IDataSource):
    def __init__(self, base_url: str = "https://data.toulouse-metropole.fr") -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "toulouse-meteo-app/1.1"})

    def fetch_weather_station_catalog(self) -> List[Station]:
        url = f"{self.base_url}/api/explore/v2.1/catalog/datasets/stations-meteo-en-place/records"
        params = {"limit": 1000}
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        stations: List[Station] = []
        for rec in data.get("results", []):
            fields = rec.get("fields", {})
            geom = rec.get("geometry", {}) or {}
            name = fields.get("nom") or fields.get("name") or fields.get("station") or "Station météo"
            id_num = fields.get("id_numero") or fields.get("numero") or fields.get("id") or ""
            lat, lon = None, None
            if "geo_point_2d" in fields and isinstance(fields["geo_point_2d"], dict):
                lat = fields["geo_point_2d"].get("lat")
                lon = fields["geo_point_2d"].get("lon")
            elif geom and geom.get("type") == "Point":
                coords = geom.get("coordinates") or [None, None]
                lon, lat = coords[0], coords[1]
            if lat is None or lon is None:
                continue
            stations.append(
                Station(
                    id=StationId(str(id_num)),
                    name=str(name),
                    latitude=float(lat),
                    longitude=float(lon),
                    kind="weather",
                    extra={"raw_fields": fields},
                )
            )
        return stations

    def fetch_metro_station_catalog(self) -> List[Station]:
        url = f"{self.base_url}/api/explore/v2.1/catalog/datasets/arret_physique/records"
        params = {"limit": 5000}
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        stations: List[Station] = []
        for rec in data.get("results", []):
            fields = rec.get("fields", {})
            geom = rec.get("geometry", {}) or {}
            mode_val = str(fields.get("mode") or fields.get("modes") or fields.get("mode_texte") or "").upper()
            if "METRO" not in mode_val:
                continue
            name = fields.get("nom") or fields.get("stop_name") or fields.get("nom_arret") or "Station"
            code = fields.get("code") or fields.get("stop_code") or fields.get("id") or name
            line = fields.get("ligne") or fields.get("line")
            lat, lon = None, None
            if "geo_point_2d" in fields and isinstance(fields["geo_point_2d"], dict):
                lat = fields["geo_point_2d"].get("lat")
                lon = fields["geo_point_2d"].get("lon")
            elif geom and geom.get("type") == "Point":
                coords = geom.get("coordinates") or [None, None]
                lon, lat = coords[0], coords[1]
            if lat is None or lon is None:
                continue
            stations.append(
                Station(
                    id=StationId(str(code)),
                    name=str(name),
                    latitude=float(lat),
                    longitude=float(lon),
                    kind="metro",
                    ligne=StationLigne(code=str(line) if line else None),
                    extra={"raw_fields": fields},
                )
            )
        return stations

    def _guess_station_dataset_id(self, weather_num: str) -> Optional[str]:
        q = f"{self.base_url}/api/explore/v2.1/catalog/datasets"
        params = {"search": f"{weather_num}-station meteo"}
        try:
            r = self.session.get(q, params=params, timeout=20)
            r.raise_for_status()
            items = r.json().get("datasets", [])
            for item in items:
                dsid = item.get("dataset_id") or item.get("datasetid") or item.get("dataset")
                if not dsid:
                    continue
                if str(dsid).startswith(f"{weather_num}-station-meteo-"):
                    return dsid
        except Exception:
            return None
        return None

    def fetch_weather_records(
        self,
        dataset_id: str,
        since: Optional[dt.datetime] = None,
        until: Optional[dt.datetime] = None,
        limit: int = 10_000,
    ) -> pd.DataFrame:
        url = f"{self.base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
        params: Dict[str, Any] = {
            "limit": limit,
            "order_by": "timestamp DESC,date DESC,datetime DESC,heure DESC",
        }
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        js = r.json()
        rows = js.get("results", [])
        if not rows:
            return pd.DataFrame()
        df = pd.json_normalize(rows)
        field_cols = [c for c in df.columns if c.startswith("fields.")]
        if field_cols:
            df = df[field_cols].rename(columns=lambda c: c.replace("fields.", ""))
        return df


class BasicCleaner(ICleaner):
    TZ = "Europe/Paris"

    def _parse_dt(self, s: Any) -> Optional[dt.datetime]:
        if pd.isna(s):
            return None
        try:
            t = pd.to_datetime(s, utc=False)
            if t.tzinfo is None:
                return t.tz_localize(self.TZ)  # type: ignore
            else:
                return t.tz_convert(self.TZ)  # type: ignore
        except Exception:
            return None

    def _col(self, df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
        for c in candidates:
            if c in df.columns:
                return c
        low = {c.lower(): c for c in df.columns}
        for c in candidates:
            if c.lower() in low:
                return low[c.lower()]
        return None

    def clean_weather_df(self, df: pd.DataFrame, station_id: StationId) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "station_id", "temperature_c", "humidity_pct", "pressure_hpa"]).set_index("timestamp")
        ts_col = self._col(df, ["timestamp", "date", "datetime", "heure", "date_heure"])
        t_col = self._col(df, ["temperature_c", "temperature", "temp", "t", "tc", "temp_c"])
        h_col = self._col(df, ["humidity_pct", "humidite", "humidity", "hum", "rh", "h"])  # relative humidity
        p_col = self._col(df, ["pressure_hpa", "pression", "pression_hpa", "p", "pa", "press"])
        out = pd.DataFrame()
        out["timestamp"] = df[ts_col] if ts_col else pd.NaT
        out["timestamp"] = out["timestamp"].map(self._parse_dt)
        out["station_id"] = station_id.value
        out["temperature_c"] = pd.to_numeric(df[t_col], errors="coerce") if t_col else np.nan
        out["humidity_pct"] = pd.to_numeric(df[h_col], errors="coerce") if h_col else np.nan
        out["pressure_hpa"] = pd.to_numeric(df[p_col], errors="coerce") if p_col else np.nan
        out = out.dropna(subset=["timestamp"]).set_index("timestamp").sort_index()
        if "humidity_pct" in out.columns:
            out["humidity_pct"] = out["humidity_pct"].clip(lower=0, upper=100)
        return out


class SimpleForecaster(IForecaster):
    def forecast(self, df: pd.DataFrame, horizon_hours: int, freq: str = "1H") -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        cols = [c for c in ["temperature_c", "humidity_pct", "pressure_hpa"] if c in df.columns]
        base = df[cols].copy()
        base = base.resample(freq).last().ffill(limit=3)
        last_idx = base.index.max()
        if pd.isna(last_idx):
            return pd.DataFrame()
        ma = base.rolling(window=3, min_periods=1).mean()
        if "temperature_c" in base.columns and len(base) >= 3:
            tail = base["temperature_c"].tail(6)
            x = np.arange(len(tail))
            if tail.notna().sum() >= 2:
                coeffs = np.polyfit(x[tail.notna()], tail[tail.notna()], 1)
                slope = coeffs[0]
            else:
                slope = 0.0
        else:
            slope = 0.0
        future_idx = pd.date_range(start=last_idx + pd.tseries.frequencies.to_offset(freq), periods=horizon_hours, freq=freq)
        fc = pd.DataFrame(index=future_idx, columns=cols, dtype=float)
        last_ma = ma.iloc[-1]
        for i, ts in enumerate(future_idx, start=1):
            for c in cols:
                val = float(last_ma.get(c)) if pd.notna(last_ma.get(c)) else np.nan
                if c == "temperature_c":
                    val = val + slope * i
                fc.loc[ts, c] = val
        return fc


class WeatherRepositoryMemory(IRepository):
    def __init__(self) -> None:
        self._store: Dict[str, pd.DataFrame] = {}

    def save_series(self, series: WeatherSeries) -> None:
        df = pd.DataFrame(
            [
                {
                    "timestamp": r.timestamp,
                    "station_id": series.station.id.value,
                    "temperature_c": r.temperature_c,
                    "humidity_pct": r.humidity_pct,
                    "pressure_hpa": r.pressure_hpa,
                }
                for r in series.records
            ]
        )
        if df.empty:
            return
        df = df.set_index("timestamp").sort_index()
        sid = series.station.id.value
        if sid in self._store and not self._store[sid].empty:
            self._store[sid] = pd.concat([self._store[sid], df]).sort_index()
        else:
            self._store[sid] = df
        self._store[sid] = self._store[sid][~self._store[sid].index.duplicated(keep="last")]

    def get_series(
        self,
        station_id: StationId,
        since: Optional[dt.datetime] = None,
        until: Optional[dt.datetime] = None,
    ) -> pd.DataFrame:
        sid = station_id.value
        df = self._store.get(sid, pd.DataFrame())
        if df.empty:
            return df
        if since is not None:
            df = df[df.index >= since]
        if until is not None:
            df = df[df.index <= until]
        return df.sort_index()


class SimpleRenderer(IRenderer):
    def show_current(self, df: pd.DataFrame) -> None:
        if df.empty:
            print("Aucune donnée météo disponible.")
            return
        last = df.iloc[-1]
        ts = df.index[-1]
        t = last.get("temperature_c")
        h = last.get("humidity_pct")
        p = last.get("pressure_hpa")
        print(f"\n— Observation la plus récente — {ts.tz_convert('Europe/Paris') if ts.tzinfo else ts}:")
        print(f"  Température: {t:.1f} °C" if pd.notna(t) else "  Température: n/d")
        print(f"  Humidité   : {h:.0f} %" if pd.notna(h) else "  Humidité   : n/d")
        print(f"  Pression   : {p:.0f} hPa" if pd.notna(p) else "  Pression   : n/d")

    def show_forecast(self, df_fc: pd.DataFrame) -> None:
        if df_fc.empty:
            print("\nPas de prévision disponible.")
            return
        print("\n— Prévision (heure par heure) —")
        for ts, row in df_fc.iterrows():
            t = row.get("temperature_c")
            h = row.get("humidity_pct")
            p = row.get("pressure_hpa")
            ts_local = ts.tz_convert('Europe/Paris') if ts.tzinfo else ts
            print(
                f"  {ts_local:%Y-%m-%d %H:%M}  T={t:.1f}°C  H={h:.0f}%  P={p:.0f}hPa"
                if all(pd.notna([t, h, p]))
                else f"  {ts_local:%Y-%m-%d %H:%M}  (valeurs partielles)"
            )


class StationCatalogSimple:
    def __init__(self, datasource: IDataSource) -> None:
        self.ds = datasource
        self._weather: List[Station] = []
        self._metro: List[Station] = []

    def load(self) -> None:
        self._weather = self.ds.fetch_weather_station_catalog()
        self._metro = self.ds.fetch_metro_station_catalog()

    def all_metro(self) -> List[Station]:
        return list(self._metro)

    def all_weather(self) -> List[Station]:
        return list(self._weather)

    def find_metro(self, name_query: str) -> Optional[Station]:
        name_query_low = name_query.strip().lower()
        if not name_query_low:
            return None
        best: Tuple[float, Optional[Station]] = (-1.0, None)
        for st in self._metro:
            n = st.name.lower()
            if name_query_low in n or n.startswith(name_query_low):
                return st
            overlap = len(set(n.split()) & set(name_query_low.split())) / max(1, len(set(name_query_low.split())))
            if overlap > best[0]:
                best = (overlap, st)
        return best[1]

    def nearest_weather_for(self, metro_station: Station) -> Optional[Station]:
        if not self._weather:
            return None
        best = None
        best_d = 1e9
        for w in self._weather:
            d = haversine_km(metro_station.latitude, metro_station.longitude, w.latitude, w.longitude)
            if d < best_d:
                best_d = d
                best = w
        return best


class WeatherIngestionService:
    def __init__(self, datasource: OpendatasoftAPIDataSource, cleaner: ICleaner, repo: IRepository, catalog: StationCatalogSimple) -> None:
        self.ds = datasource
        self.cleaner = cleaner
        self.repo = repo
        self.catalog = catalog

    def ingest_station(self, weather_station: Station, hours: int = 24) -> pd.DataFrame:
        num = "".join([c for c in weather_station.id.value if c.isdigit()])
        dsid = self.ds._guess_station_dataset_id(num) if num else None
        if not dsid:
            raise RuntimeError(f"Impossible de déterminer le dataset pour la station météo {weather_station.name} (id={weather_station.id.value}).")
        until = pd.Timestamp.now(tz="Europe/Paris")
        since = until - pd.Timedelta(hours=hours)
        raw = self.ds.fetch_weather_records(dataset_id=dsid, since=since.to_pydatetime(), until=until.to_pydatetime())
        clean = self.cleaner.clean_weather_df(raw, weather_station.id)
        clean = clean[(clean.index >= since) & (clean.index <= until)]
        records = [
            WeatherRecord(
                station_id=weather_station.id,
                timestamp=ts,
                temperature_c=float(row["temperature_c"]) if pd.notna(row.get("temperature_c")) else None,
                humidity_pct=float(row["humidity_pct"]) if pd.notna(row.get("humidity_pct")) else None,
                pressure_hpa=float(row["pressure_hpa"]) if pd.notna(row.get("pressure_hpa")) else None,
            )
            for ts, row in clean.iterrows()
        ]
        series = WeatherSeries(station=weather_station, records=records)
        self.repo.save_series(series)
        return clean


class WeatherQueryService:
    def __init__(self, repo: IRepository, renderer: IRenderer) -> None:
        self.repo = repo
        self.renderer = renderer

    def show_current_for(self, station: Station) -> pd.DataFrame:
        df = self.repo.get_series(station.id)
        self.renderer.show_current(df)
        return df


class ForecastService:
    def __init__(self, repo: IRepository, forecaster: IForecaster, renderer: IRenderer) -> None:
        self.repo = repo
        self.forecaster = forecaster
        self.renderer = renderer

    def forecast_for(self, station: Station, horizon_hours: int = 6) -> pd.DataFrame:
        df = self.repo.get_series(station.id)
        fc = self.forecaster.forecast(df, horizon_hours=horizon_hours, freq="1H")
        self.renderer.show_forecast(fc)
        return fc


class YDataSDKQuality:
    def __init__(self, enabled: bool = _HAS_YDATA_SDK) -> None:
        self.enabled = enabled

    def quality_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {"rows": 0}
        res: Dict[str, Any] = {}
        res["rows"] = int(len(df))
        res["missing_rate"] = float(df.isna().mean().mean())
        res["duplicate_index"] = int(df.index.duplicated().sum())
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        res["numeric_cols"] = num_cols
        if num_cols:
            z = ((df[num_cols] - df[num_cols].mean()) / df[num_cols].std(ddof=0)).abs()
            res["outlier_counts_z3"] = {c: int((z[c] > 3).sum()) for c in num_cols}
            corr = df[num_cols].corr().abs()
            upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            redundant = [(i, j, float(upper.loc[i, j])) for i in upper.index for j in upper.columns if pd.notna(upper.loc[i, j]) and upper.loc[i, j] > 0.95]
            res["redundant_pairs_abs>0.95"] = redundant
        text_cols = df.select_dtypes(include=[object]).columns.tolist()
        if text_cols:
            invalid = {c: int(df[c].astype(str).str.strip().eq("").sum()) for c in text_cols}
            res["empty_text_counts"] = invalid
        return res

    def synthesize(self, df: pd.DataFrame, n: int = 100) -> pd.DataFrame:
        if df.empty or n <= 0:
            return pd.DataFrame()
        out = []
        rng = np.random.default_rng(42)
        for _ in range(n):
            row: Dict[str, Any] = {}
            for c in df.columns:
                s = df[c]
                if pd.api.types.is_numeric_dtype(s):
                    mu = float(s.mean()) if s.notna().any() else 0.0
                    sigma = float(s.std(ddof=0)) if s.notna().sum() > 1 else 1.0
                    row[c] = float(rng.normal(mu, sigma))
                else:
                    vals = s.dropna().unique().tolist()
                    row[c] = rng.choice(vals).item() if vals else None
            out.append(row)
        syn = pd.DataFrame(out)
        if df.index.name is not None:
            syn.index.name = df.index.name
        return syn


class DataProfiler:
    def __init__(self, use_sdk: bool = _HAS_YDATA_SDK, use_profiling: bool = _HAS_PROFILING) -> None:
        self.use_sdk = use_sdk
        self.use_profiling = use_profiling
        self.sdkq = YDataSDKQuality(enabled=use_sdk)

    def profile(self, df: pd.DataFrame, out_html: str = "rapport.html", synthetic_rows: int = 0) -> Optional[str]:
        q = self.sdkq.quality_summary(df)
        print("\nQualité (résumé)", q)
        if synthetic_rows > 0:
            syn = self.sdkq.synthesize(df, n=synthetic_rows)
            print(f"\nDonnées synthétiques générées: {len(syn)} lignes")
        if self.use_profiling and not df.empty:
            try:
                profile = ProfileReport(df.reset_index(), title="Toulouse Météo — Profiling", minimal=True)
                profile.to_file(out_html)
                return os.path.abspath(out_html)
            except Exception:
                return None
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Toulouse météo — API only (OOP, SOLID)")
    parser.add_argument("--metro", type=str, default="Capitole", help="Nom (partiel) de la station de métro Tisséo — défaut: Capitole")
    parser.add_argument("--hours", type=int, default=24, help="Fenêtre d'historique à ingérer (heures)")
    parser.add_argument("--forecast", type=int, default=6, help="Horizon de prévision (heures)")
    parser.add_argument("--profile", action="store_true", help="Générer un rapport de profil (HTML) et un résumé qualité")
    parser.add_argument("--synthetic", type=int, default=0, help="Nombre de lignes synthétiques à générer (0 = désactivé)")
    parser.add_argument("--base-url", type=str, default="https://data.toulouse-metropole.fr", help="Base URL Opendatasoft")

    args = parser.parse_args()

    ds = OpendatasoftAPIDataSource(base_url=args.base_url)
    cleaner = BasicCleaner()
    repo = WeatherRepositoryMemory()
    renderer = SimpleRenderer()
    catalog = StationCatalogSimple(ds)
    catalog.load()

    metro = catalog.find_metro(args.metro)
    if not metro:
        raise SystemExit(f"Station métro introuvable pour la requête: {args.metro}")
    print(f"Station métro sélectionnée: {metro.name} ({metro.latitude:.5f},{metro.longitude:.5f})")

    weather = catalog.nearest_weather_for(metro)
    if not weather:
        raise SystemExit("Aucune station météo disponible.")
    print(f"Station météo la plus proche: {weather.name} #{weather.id.value} ({weather.latitude:.5f},{weather.longitude:.5f})")

    ingest = WeatherIngestionService(ds, cleaner, repo, catalog)
    df_clean = ingest.ingest_station(weather, hours=args.hours)

    query = WeatherQueryService(repo, renderer)
    _ = query.show_current_for(weather)

    fc_service = ForecastService(repo, SimpleForecaster(), renderer)
    _ = fc_service.forecast_for(weather, horizon_hours=args.forecast)

    if args.profile:
        profiler = DataProfiler(use_sdk=_HAS_YDATA_SDK, use_profiling=_HAS_PROFILING)
        out = profiler.profile(df_clean, out_html="rapport.html", synthetic_rows=args.synthetic)
        if out:
            print(f"\nProfil HTML: {out}")


if __name__ == "__main__":
    main()
