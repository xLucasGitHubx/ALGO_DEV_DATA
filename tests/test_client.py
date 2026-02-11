"""Tests pour le client HTTP ODSClient (avec mocks)."""

from unittest.mock import patch, MagicMock
from meteo_toulouse.client import ODSClient


class TestODSClientInit:
    def test_default_url(self):
        client = ODSClient()
        assert "toulouse-metropole" in client.base_url

    def test_custom_url(self):
        client = ODSClient(base_url="https://example.com/api")
        assert client.base_url == "https://example.com/api"

    def test_trailing_slash_removed(self):
        client = ODSClient(base_url="https://example.com/api/")
        assert not client.base_url.endswith("/")


class TestODSClientCatalog:
    @patch.object(ODSClient, "_request")
    def test_catalog_datasets_page(self, mock_request):
        mock_request.return_value = {
            "total_count": 1,
            "results": [{"dataset_id": "test-ds"}],
        }
        client = ODSClient()
        result = client.catalog_datasets_page(limit=10, offset=0)
        assert result["total_count"] == 1
        assert len(result["results"]) == 1
        mock_request.assert_called_once()

    @patch.object(ODSClient, "catalog_datasets_page")
    def test_catalog_datasets_iter(self, mock_page):
        mock_page.return_value = {
            "total_count": 2,
            "results": [
                {"dataset_id": "ds-1"},
                {"dataset_id": "ds-2"},
            ],
        }
        client = ODSClient()
        datasets = list(client.catalog_datasets_iter(hard_limit=10))
        assert len(datasets) == 2
        assert datasets[0]["dataset_id"] == "ds-1"

    @patch.object(ODSClient, "catalog_datasets_page")
    def test_catalog_datasets_iter_hard_limit(self, mock_page):
        mock_page.return_value = {
            "total_count": 100,
            "results": [{"dataset_id": f"ds-{i}"} for i in range(100)],
        }
        client = ODSClient()
        datasets = list(client.catalog_datasets_iter(hard_limit=3))
        assert len(datasets) == 3


class TestODSClientDataset:
    @patch.object(ODSClient, "_request")
    def test_dataset_info(self, mock_request):
        mock_request.return_value = {"dataset_id": "test", "fields": []}
        client = ODSClient()
        result = client.dataset_info("test")
        assert result["dataset_id"] == "test"
        mock_request.assert_called_once_with("GET", "/catalog/datasets/test")


class TestODSClientRecords:
    @patch.object(ODSClient, "_request")
    def test_iter_records(self, mock_request):
        mock_request.return_value = {
            "results": [
                {"temperature": 20.0},
                {"temperature": 21.0},
            ],
        }
        client = ODSClient()
        records = list(client.iter_records("test-ds", max_rows=5))
        assert len(records) == 2
        assert records[0]["temperature"] == 20.0

    @patch.object(ODSClient, "_request")
    def test_iter_records_max_rows(self, mock_request):
        mock_request.return_value = {
            "results": [{"temperature": i} for i in range(10)],
        }
        client = ODSClient()
        records = list(client.iter_records("test-ds", max_rows=3))
        assert len(records) == 3

    @patch.object(ODSClient, "_request")
    def test_iter_records_empty(self, mock_request):
        mock_request.return_value = {"results": []}
        client = ODSClient()
        records = list(client.iter_records("test-ds"))
        assert records == []
