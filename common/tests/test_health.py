from unittest.mock import patch

from django.db import OperationalError
from django.urls import reverse
from rest_framework.test import APIClient


def test_health_check_returns_ok(api_client: APIClient) -> None:
    response = api_client.get(reverse("health-check"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_503_when_db_unavailable(api_client: APIClient) -> None:
    with patch("common.views.connection") as mock_conn:
        mock_conn.ensure_connection.side_effect = OperationalError("DB unreachable")
        response = api_client.get("/health/ready/")
    assert response.status_code == 503
    assert response.json() == {"status": "error"}


def test_readiness_check_returns_200_when_db_reachable(api_client: APIClient, db) -> None:
    response = api_client.get("/health/ready/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_schema_endpoint_returns_200(api_client: APIClient) -> None:
    response = api_client.get("/api/schema/")
    assert response.status_code == 200


def test_swagger_ui_returns_200(api_client: APIClient) -> None:
    response = api_client.get("/api/docs/")
    assert response.status_code == 200


def test_redoc_returns_200(api_client: APIClient) -> None:
    response = api_client.get("/api/redoc/")
    assert response.status_code == 200
