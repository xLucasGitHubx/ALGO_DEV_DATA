"""
Command Pattern: Menu interactif de selection de station.
"""

from __future__ import annotations

from meteo_toulouse.config import PRINT_WIDTH
from meteo_toulouse.models import Station
from meteo_toulouse.utils import norm
from meteo_toulouse.repository import WeatherRepositoryMemory
from meteo_toulouse.services.forecast import ForecastService
from meteo_toulouse.services.query import WeatherQueryService
from meteo_toulouse.services.ingestion import WeatherIngestionService
from meteo_toulouse.ui.renderer import SimpleRenderer
from meteo_toulouse.ui.carousel import StationCarouselRenderer


class StationSelectorMenu:
    """
    Command Pattern: Menu interactif de selection de station.

    Permet a l'utilisateur de:
    - Voir la liste des stations
    - Consulter une station specifique par numero
    - Rechercher une station par nom
    - Lancer le carrousel

    Avec chargement a la demande:
    Les observations d'une station ne sont chargees que lors de la consultation,
    permettant un demarrage rapide et des donnees toujours fraiches.
    """

    def __init__(
        self,
        repo: WeatherRepositoryMemory,
        forecast: ForecastService,
        query: WeatherQueryService,
        carousel_delay: int = 5,
        ingestion_service: WeatherIngestionService | None = None
    ) -> None:
        self.repo = repo
        self.forecast = forecast
        self.query = query
        self.carousel_delay = carousel_delay
        self._ingestion = ingestion_service
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
        query_norm = norm(query)
        results: list[tuple[int, Station]] = []

        for i, st in enumerate(self._stations_list, 1):
            name_norm = norm(st.name)
            if query_norm in name_norm:
                results.append((i, st))

        return results

    def _show_station_detail(self, station: Station) -> None:
        """Affiche le detail d'une station.

        Si le service d'ingestion est disponible, charge les observations
        a la demande avant l'affichage (avec support du cache TTL).
        """
        # Chargement a la demande des observations
        if self._ingestion:
            # Verifier si le cache est valide (si repository supporte le cache)
            needs_load = True
            if hasattr(self.repo, 'needs_refresh'):
                needs_load = self.repo.needs_refresh(station.id)
                if not needs_load:
                    print(f"\n[Cache] Utilisation des donnees en cache pour '{station.name}'")

            if needs_load:
                print(f"\n[Chargement] Recuperation des observations pour '{station.name}'...")
                try:
                    count = self._ingestion.ingest_latest(station, max_rows=5)
                    if hasattr(self.repo, 'mark_refreshed'):
                        self.repo.mark_refreshed(station.id)
                    print(f"[OK] {count} observation(s) chargee(s).")
                except Exception as e:
                    print(f"[Erreur] Impossible de charger les observations: {e}")
                    return

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
