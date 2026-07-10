import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def taskflow_exception_handler(exc: Exception, context: dict) -> Response | None:
    """Normalise all DRF error responses to a single shape.

    DRF returns errors in several different shapes depending on the error type:
    - ``{"detail": "Not found."}`` for 404 / permission errors
    - ``{"field": ["error message"]}`` for serializer validation errors
    - ``{"non_field_errors": ["..."]}`` for non-field validation errors

    This handler wraps DRF's default handler and re-shapes every response to::

        {"errors": {"field": ["message"], ...}}

    Single ``detail`` responses become::

        {"errors": {"non_field_errors": ["message"]}}

    Unhandled exceptions (500s) are left to Django's default handling.
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict) and list(data.keys()) == ["detail"]:
        normalized: dict = {"errors": {"non_field_errors": [str(data["detail"])]}}
    elif isinstance(data, dict):
        normalized = {"errors": data}
    elif isinstance(data, list):
        normalized = {"errors": {"non_field_errors": data}}
    else:
        normalized = {"errors": {"non_field_errors": [str(data)]}}

    response.data = normalized
    return response
