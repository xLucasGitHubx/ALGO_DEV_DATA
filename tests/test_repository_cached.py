"""Tests pour le repository CachedWeatherRepository."""

from datetime import datetime, timedelta
from time import sleep
from meteo_toulouse.models import Station, WeatherRecord
from meteo_toulouse.repository_cached import CachedWeatherRepository


def _make_station(sid: str = "st-01", name: str = "Test Station") -> Station:
    """Helper pour creer une station de test."""
    return Station(id=sid, name=name, dataset_id=sid)


def _make_record(sid: str = "st-01", temp: float = 20.0, ts: datetime | None = None) -> WeatherRecord:
    """Helper pour creer un enregistrement de test."""
    return WeatherRecord(station_id=sid, temperature_c=temp, timestamp=ts)


class TestCachedRepositoryInit:
    """Tests d'initialisation du repository avec cache."""

    def test_init_default_ttl(self):
        """Verifie que le TTL par defaut est de 300 secondes."""
        repo = CachedWeatherRepository()
        assert repo._ttl == timedelta(seconds=300)

    def test_init_custom_ttl(self):
        """Verifie que le TTL personnalise est applique."""
        repo = CachedWeatherRepository(ttl_seconds=60)
        assert repo._ttl == timedelta(seconds=60)

    def test_init_empty_cache(self):
        """Verifie que le cache est vide a l'initialisation."""
        repo = CachedWeatherRepository()
        assert len(repo._last_load) == 0


class TestNeedsRefresh:
    """Tests de la verification d'expiration du cache."""

    def test_needs_refresh_never_loaded(self):
        """Une station jamais chargee necessite un refresh."""
        repo = CachedWeatherRepository()
        assert repo.needs_refresh("st-01") is True

    def test_needs_refresh_just_loaded(self):
        """Une station fraichement chargee ne necessite pas de refresh."""
        repo = CachedWeatherRepository(ttl_seconds=60)
        repo.mark_refreshed("st-01")
        assert repo.needs_refresh("st-01") is False

    def test_needs_refresh_after_ttl_expired(self):
        """Une station dont le TTL est expire necessite un refresh."""
        repo = CachedWeatherRepository(ttl_seconds=1)
        repo.mark_refreshed("st-01")
        sleep(1.1)  # Attendre l'expiration du TTL
        assert repo.needs_refresh("st-01") is True

    def test_needs_refresh_multiple_stations(self):
        """Verifie le cache independant pour plusieurs stations."""
        repo = CachedWeatherRepository(ttl_seconds=60)
        repo.mark_refreshed("st-01")
        assert repo.needs_refresh("st-01") is False
        assert repo.needs_refresh("st-02") is True


class TestMarkRefreshed:
    """Tests de marquage du cache."""

    def test_mark_refreshed_updates_timestamp(self):
        """Verifie que mark_refreshed met a jour le timestamp."""
        repo = CachedWeatherRepository()
        repo.mark_refreshed("st-01")
        assert "st-01" in repo._last_load
        assert isinstance(repo._last_load["st-01"], datetime)

    def test_mark_refreshed_resets_ttl(self):
        """Verifie que mark_refreshed reinitialise le TTL."""
        repo = CachedWeatherRepository(ttl_seconds=2)
        repo.mark_refreshed("st-01")
        sleep(1)  # Attendre 1 seconde
        assert repo.needs_refresh("st-01") is False
        repo.mark_refreshed("st-01")  # Reinitialiser
        sleep(1)  # Attendre encore 1 seconde
        assert repo.needs_refresh("st-01") is False  # Toujours valide


class TestClearCache:
    """Tests de vidage du cache."""

    def test_clear_cache_single_station(self):
        """Verifie le vidage du cache pour une seule station."""
        repo = CachedWeatherRepository()
        repo.mark_refreshed("st-01")
        repo.mark_refreshed("st-02")
        repo.clear_cache("st-01")
        assert repo.needs_refresh("st-01") is True
        assert repo.needs_refresh("st-02") is False

    def test_clear_cache_all_stations(self):
        """Verifie le vidage complet du cache."""
        repo = CachedWeatherRepository()
        repo.mark_refreshed("st-01")
        repo.mark_refreshed("st-02")
        repo.clear_cache()
        assert repo.needs_refresh("st-01") is True
        assert repo.needs_refresh("st-02") is True

    def test_clear_cache_nonexistent_station(self):
        """Verifie qu'effacer une station inexistante ne leve pas d'erreur."""
        repo = CachedWeatherRepository()
        repo.clear_cache("st-99")  # Ne doit pas lever d'exception
        assert repo.needs_refresh("st-99") is True


class TestGetCacheInfo:
    """Tests des informations sur l'etat du cache."""

    def test_get_cache_info_not_cached(self):
        """Verifie les infos pour une station non en cache."""
        repo = CachedWeatherRepository()
        info = repo.get_cache_info("st-01")
        assert info["cached"] is False
        assert info["last_load"] is None
        assert info["time_remaining"] is None
        assert info["expired"] is True

    def test_get_cache_info_cached_valid(self):
        """Verifie les infos pour une station en cache valide."""
        repo = CachedWeatherRepository(ttl_seconds=60)
        repo.mark_refreshed("st-01")
        info = repo.get_cache_info("st-01")
        assert info["cached"] is True
        assert info["last_load"] is not None
        assert info["expired"] is False

    def test_get_cache_info_cached_expired(self):
        """Verifie les infos pour une station en cache expire."""
        repo = CachedWeatherRepository(ttl_seconds=1)
        repo.mark_refreshed("st-01")
        sleep(1.1)
        info = repo.get_cache_info("st-01")
        assert info["cached"] is True
        assert info["last_load"] is not None
        assert info["expired"] is True
        assert info["time_remaining"] == "expired"


class TestCachedRepositoryInheritance:
    """Tests de l'heritage du repository de base."""

    def test_inherits_upsert_station(self):
        """Verifie que upsert_station fonctionne."""
        repo = CachedWeatherRepository()
        st = _make_station()
        repo.upsert_station(st)
        assert repo.get_station("st-01") == st

    def test_inherits_add_record(self):
        """Verifie que add_record fonctionne."""
        repo = CachedWeatherRepository()
        st = _make_station()
        repo.upsert_station(st)
        rec = _make_record()
        repo.add_record("st-01", rec)
        records = repo.latest_records("st-01", n=1)
        assert len(records) == 1
        assert records[0] == rec

    def test_inherits_latest_records(self):
        """Verifie que latest_records fonctionne avec le cache."""
        repo = CachedWeatherRepository()
        st = _make_station()
        repo.upsert_station(st)

        # Ajouter des enregistrements
        rec1 = _make_record(ts=datetime(2025, 1, 1, 12, 0))
        rec2 = _make_record(ts=datetime(2025, 1, 1, 13, 0), temp=22.0)
        repo.add_record("st-01", rec1)
        repo.add_record("st-01", rec2)

        # Recuperer les enregistrements
        records = repo.latest_records("st-01", n=2)
        assert len(records) == 2
        assert records[0].temperature_c == 22.0  # Plus recent en premier


class TestCacheBehaviorIntegration:
    """Tests d'integration du comportement du cache."""

    def test_lazy_loading_workflow(self):
        """Simule le workflow de chargement a la demande."""
        repo = CachedWeatherRepository(ttl_seconds=60)
        st = _make_station()
        repo.upsert_station(st)

        # Premiere consultation: cache vide, doit charger
        assert repo.needs_refresh("st-01") is True

        # Simuler le chargement des donnees
        rec = _make_record()
        repo.add_record("st-01", rec)
        repo.mark_refreshed("st-01")

        # Deuxieme consultation: cache valide, pas de rechargement
        assert repo.needs_refresh("st-01") is False

        # Les donnees sont toujours disponibles
        records = repo.latest_records("st-01", n=1)
        assert len(records) == 1

    def test_cache_expiration_workflow(self):
        """Simule l'expiration du cache et le rechargement."""
        repo = CachedWeatherRepository(ttl_seconds=1)
        st = _make_station()
        repo.upsert_station(st)

        # Chargement initial
        rec1 = _make_record(temp=20.0)
        repo.add_record("st-01", rec1)
        repo.mark_refreshed("st-01")
        assert repo.needs_refresh("st-01") is False

        # Attendre l'expiration
        sleep(1.1)
        assert repo.needs_refresh("st-01") is True

        # Rechargement avec nouvelles donnees
        rec2 = _make_record(temp=25.0)
        repo.add_record("st-01", rec2)
        repo.mark_refreshed("st-01")

        # Verifier que les nouvelles donnees sont disponibles
        records = repo.latest_records("st-01", n=2)
        assert len(records) == 2  # Anciennes + nouvelles donnees
