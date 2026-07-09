import logging

from django.db.models import Count, Q, QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from projects.filters import ProjectFilter, TaskFilter
from projects.models import Project, Task
from projects.serializers import (
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectWriteSerializer,
    TaskSerializer,
)

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD for projects, plus a summary action with task aggregates."""

    filterset_class = ProjectFilter
    search_fields = ["name", "description"]
    ordering_fields = ["created", "name", "status"]
    ordering = ["-created"]

    def get_queryset(self) -> QuerySet[Project]:
        queryset = Project.objects.all()
        if self.action == "list":
            # Annotate once instead of counting per row in the serializer.
            return queryset.annotate(_task_count=Count("tasks"))
        if self.action == "retrieve":
            # Reverse FK: prefetch to avoid N+1 when nesting tasks.
            return queryset.prefetch_related("tasks")
        return queryset

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return ProjectListSerializer
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return ProjectWriteSerializer

    @action(detail=True, methods=["get"])
    def summary(self, request: Request, pk: str | None = None) -> Response:
        """Return task totals for a project computed in a single annotated query."""
        if pk is None:
            return Response(
                {"detail": "Project not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        row = (
            Project.objects.filter(pk=pk)
            .annotate(
                total_tasks=Count("tasks"),
                completed_tasks=Count("tasks", filter=Q(tasks__is_complete=True)),
            )
            .values("id", "name", "total_tasks", "completed_tasks")
            .first()
        )
        if row is None:
            return Response(
                {"detail": "Project not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        total = row["total_tasks"]
        completed = row["completed_tasks"]
        return Response(
            {
                "id": str(row["id"]),
                "name": row["name"],
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round(completed / total, 2) if total else 0.0,
            }
        )


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD for tasks with filtering by project, priority, and completion."""

    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    search_fields = ["title", "assignee"]
    ordering_fields = ["created", "priority", "due_date"]
    ordering = ["-created"]

    def get_queryset(self) -> QuerySet[Task]:
        # Forward FK: select_related avoids a query per task for project data.
        return Task.objects.select_related("project")
