import pytest
from rest_framework.test import APIClient

from projects.models import Project


@pytest.fixture
def project(db) -> Project:
    return Project.objects.create(name="Alpha")


def test_404_response_has_errors_key(api_client: APIClient, db) -> None:
    response = api_client.get("/api/projects/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404
    body = response.json()
    assert "errors" in body
    assert "non_field_errors" in body["errors"]


def test_validation_error_response_has_errors_key(api_client: APIClient, db) -> None:
    response = api_client.post("/api/projects/", {"name": "   "}, format="json")
    assert response.status_code == 400
    body = response.json()
    assert "errors" in body
    assert "name" in body["errors"]


def test_400_does_not_expose_detail_at_top_level(api_client: APIClient, db) -> None:
    response = api_client.post("/api/projects/", {"name": "   "}, format="json")
    assert "detail" not in response.json()


def test_404_does_not_expose_detail_at_top_level(api_client: APIClient, db) -> None:
    response = api_client.get("/api/projects/00000000-0000-0000-0000-000000000000/")
    assert "detail" not in response.json()
