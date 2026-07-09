from django.http import HttpRequest, JsonResponse


def health_check(request: HttpRequest) -> JsonResponse:
    """Liveness probe for load balancers and uptime monitors."""
    return JsonResponse({"status": "ok"})
