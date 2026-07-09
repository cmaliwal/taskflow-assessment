import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """A DRF test client shared across API tests."""
    return APIClient()
