"""
Client/Adapter Pattern: Abstraction de l'API Opendatasoft.

Encapsule les appels HTTP vers l'API Explore v2.1 de Toulouse Metropole.
"""

from __future__ import annotations

from collections.abc import Iterator

import requests

from meteo_toulouse.config import (
    APP_CONFIG,
    DEFAULT_BASE_URL,
    HTTP_TIMEOUT,
    CATALOG_PAGE_SIZE,
    CATALOG_HARD_LIMIT,
    RECORDS_PAGE_SIZE,
    JSONLike,
)


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
