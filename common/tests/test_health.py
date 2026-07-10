from django.urls import reverse
from rest_framework.test import APIClient


def test_health_check_returns_ok(api_client: APIClient) -> None:
    response = api_client.get(reverse("health-check"))
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
