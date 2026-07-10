import contextvars
import logging
import uuid

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestIdMiddleware:
    """Attach a unique request_id to every request for log correlation.

    Reads ``X-Request-ID`` from the incoming request headers (useful when a
    load balancer or API gateway injects an ID). Falls back to a new UUID4 if
    the header is absent.

    The ID is stored in ``request_id_var`` (a ContextVar) so any logger in
    the request lifecycle can include it without it being passed explicitly.
    The same ID is echoed back in the ``X-Request-ID`` response header so
    clients can correlate their requests with server-side log lines.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = request_id
        return response
