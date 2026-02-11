"""
Strategy Pattern: Rendu console simple des donnees meteo.
"""

from __future__ import annotations

from meteo_toulouse.config import JSONLike, PRINT_WIDTH
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository import WeatherRepositoryMemory


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
