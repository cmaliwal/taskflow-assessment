"""Documented ORM optimization patterns used across the taskflow API.

Each function states its query bounds so a reviewer can verify efficiency
without running the code. The regression suite in
``projects/tests/test_orm_examples.py`` asserts these bounds with
``django_assert_num_queries``.
"""

import logging

from django.db.models import Count, Q, QuerySet

from projects.models import Project, Task

logger = logging.getLogger(__name__)


def projects_with_task_stats() -> QuerySet[Project]:
    """Annotate each project with task aggregates in one query.

    Query bounds: exactly one SQL query regardless of the number of projects or
    tasks. This replaces the naive N+1 pattern below, where every project
    triggers its own ``COUNT`` query::

        # Naive: 1 + N queries (one COUNT per project)
        for project in Project.objects.all():
            total = project.tasks.count()
            done = project.tasks.filter(is_complete=True).count()

    Pushing the aggregation into the database with ``annotate`` collapses that
    into a single ``GROUP BY`` query.
    """
    return Project.objects.annotate(
        total_tasks=Count("tasks"),
        completed_tasks=Count("tasks", filter=Q(tasks__is_complete=True)),
    )


def tasks_with_projects() -> QuerySet[Task]:
    """Fetch tasks joined to their parent project (forward FK).

    Query bounds: one query. ``select_related`` is correct here because each
    task has exactly one project, so a SQL JOIN fetches both in a single round
    trip. Without it, reading ``task.project`` in a loop is a classic N+1.
    """
    return Task.objects.select_related("project")


def projects_with_prefetched_tasks() -> QuerySet[Project]:
    """Fetch projects with their tasks (reverse FK) using prefetch_related.

    Query bounds: two queries total (one for projects, one for all their
    tasks), independent of project count. ``prefetch_related`` is correct here
    rather than ``select_related`` because each project has many tasks; a JOIN
    would multiply project rows by task rows.
    """
    return Project.objects.prefetch_related("tasks")


def high_priority_task_ids(project_id: str, limit: int = 100) -> list[str]:
    """Return ids of a project's incomplete high-priority tasks, most recent first.

    Query bounds: one query, capped at ``limit`` rows. Projects only the ``id``
    column via ``values_list`` instead of hydrating full model instances, and
    slices before evaluation so the SQL carries a ``LIMIT``.
    """
    return [
        str(task_id)
        for task_id in Task.objects.filter(
            project_id=project_id,
            is_complete=False,
            priority__gte=Task.Priority.HIGH,
        )
        .order_by("-created")
        .values_list("id", flat=True)[:limit]
    ]
