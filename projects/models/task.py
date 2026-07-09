from django.db import models

from common.models import BaseModel


class TaskQuerySet(models.QuerySet["Task"]):
    """QuerySet that encapsulates reusable queryset operations for Task."""

    def with_project(self) -> "TaskQuerySet":
        """Join to the parent project via a single SQL JOIN (forward FK)."""
        return self.select_related("project")


class TaskManager(models.Manager["Task"]):
    """Default manager for Task, backed by TaskQuerySet."""

    def get_queryset(self) -> TaskQuerySet:
        return TaskQuerySet(self.model, using=self._db)

    def with_project(self) -> TaskQuerySet:
        return self.get_queryset().with_project()


class Task(BaseModel):
    """A unit of work belonging to a project."""

    objects: TaskManager = TaskManager()  # type: ignore[assignment]

    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"
        CRITICAL = 4, "Critical"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    title = models.CharField(max_length=255)
    assignee = models.CharField(max_length=150, blank=True)
    priority = models.PositiveSmallIntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    due_date = models.DateField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        indexes = BaseModel.Meta.indexes + [
            models.Index(fields=["project", "is_complete"]),
        ]

    def __str__(self) -> str:
        return self.title
