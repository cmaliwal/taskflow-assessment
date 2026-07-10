from django.db import models
from django.db.models import Count

from common.models import BaseModel


class ProjectQuerySet(models.QuerySet["Project"]):
    """QuerySet that encapsulates reusable queryset operations for Project."""

    def with_task_stats(self) -> "ProjectQuerySet":
        """Annotate each project with its task count in a single GROUP BY query.

        The annotation is named ``_task_count`` to match the ``source`` in
        ``ProjectListSerializer``. Using a leading underscore signals that this
        is a computed attribute, not a model field.
        """
        return self.annotate(_task_count=Count("tasks"))

    def with_tasks(self) -> "ProjectQuerySet":
        """Prefetch tasks for the reverse FK (two queries total, N+1-free)."""
        return self.prefetch_related("tasks")


class ProjectManager(models.Manager["Project"]):
    """Default manager for Project, backed by ProjectQuerySet."""

    def get_queryset(self) -> ProjectQuerySet:
        return ProjectQuerySet(self.model, using=self._db)

    def with_task_stats(self) -> ProjectQuerySet:
        return self.get_queryset().with_task_stats()

    def with_tasks(self) -> ProjectQuerySet:
        return self.get_queryset().with_tasks()


class Project(BaseModel):
    """A project that groups related tasks."""

    objects: ProjectManager = ProjectManager()  # type: ignore[assignment]

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_HOLD = "on_hold", "On hold"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta(BaseModel.Meta):
        indexes = BaseModel.Meta.indexes + [
            models.Index(fields=["status", "-created"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["name"], name="project_name_unique"),
        ]

    def __str__(self) -> str:
        return self.name
