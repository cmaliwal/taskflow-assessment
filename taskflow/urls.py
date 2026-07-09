from django.contrib import admin
from django.urls import include, path

from common.views import health_check, readiness_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("health/ready/", readiness_check, name="health-readiness"),
    path("api/", include("projects.urls")),
]
