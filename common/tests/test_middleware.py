import uuid

from rest_framework.test import APIClient


def test_response_includes_request_id_header(api_client: APIClient) -> None:
    response = api_client.get("/health/")
    assert "X-Request-ID" in response


def test_response_echoes_supplied_request_id(api_client: APIClient) -> None:
    custom_id = str(uuid.uuid4())
    response = api_client.get("/health/", HTTP_X_REQUEST_ID=custom_id)
    assert response["X-Request-ID"] == custom_id


def test_response_generates_request_id_when_absent(api_client: APIClient) -> None:
    response = api_client.get("/health/")
    header_value = response["X-Request-ID"]
    uuid.UUID(header_value)
