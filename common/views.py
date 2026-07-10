import logging

from django.db import OperationalError, connection
from django.http import HttpRequest, JsonResponse

logger = logging.getLogger(__name__)


def health_check(request: HttpRequest) -> JsonResponse:
    """Liveness probe for load balancers and orchestrators.

    Only checks that the process is running. Intentionally does NOT check
    the database - if the DB is down, the process is still alive and should
    not be restarted.
    """
    return JsonResponse({"status": "ok"})


def readiness_check(request: HttpRequest) -> JsonResponse:
    """Readiness probe that verifies database connectivity.

    Returns 200 when the app can serve traffic, 503 when it cannot.
    Orchestrators (Kubernetes) use readiness probes to route traffic; they
    use liveness probes to decide whether to restart a pod.
    """
    try:
        connection.ensure_connection()
    except OperationalError:
        logger.exception("Readiness check failed: cannot connect to the database")
        return JsonResponse({"status": "error"}, status=503)
    return JsonResponse({"status": "ok"})
