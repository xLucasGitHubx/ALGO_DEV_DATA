"""
Point d'entree principal de l'application Meteo Toulouse.
"""

from __future__ import annotations

import os
import sys

import requests

from meteo_toulouse.config import APP_CONFIG, PRINT_WIDTH
from meteo_toulouse.models import Station
from meteo_toulouse.client import ODSClient
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.cleaner import BasicCleaner
from meteo_toulouse.services.catalog import StationCatalogSimple
from meteo_toulouse.services.ingestion import WeatherIngestionService
from meteo_toulouse.services.query import WeatherQueryService
from meteo_toulouse.services.forecast import ForecastService
from meteo_toulouse.ui.renderer import SimpleRenderer
from meteo_toulouse.ui.menu import StationSelectorMenu


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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur.")
        sys.exit(0)
