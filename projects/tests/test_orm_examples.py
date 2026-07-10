import datetime

import pytest

from projects.models import Project, Task
from projects.orm_examples import (
    high_priority_task_ids,
    projects_with_prefetched_tasks,
    projects_with_task_stats,
    tasks_with_projects,
)


@pytest.fixture
def seeded(db) -> list[Project]:
    projects = [Project.objects.create(name=f"Project {i}") for i in range(3)]
    for project in projects:
        Task.objects.bulk_create(
            [
                Task(
                    project=project,
                    title=f"Task {j}",
                    is_complete=j == 0,
                    due_date=datetime.date(2026, 7, j + 1),
                )
                for j in range(4)
            ]
        )
    return projects


def test_projects_with_task_stats_uses_single_query(
    seeded: list[Project], django_assert_num_queries
) -> None:
    with django_assert_num_queries(1):
        # django-stubs cannot see runtime annotations inside .values().
        rows = list(
            projects_with_task_stats().values(  # type: ignore[misc]
                "name", "total_tasks", "completed_tasks", "latest_due_date"
            )
        )
    assert len(rows) == 3
    assert all(row["total_tasks"] == 4 for row in rows)
    assert all(row["completed_tasks"] == 1 for row in rows)
    assert all(row["latest_due_date"] == datetime.date(2026, 7, 4) for row in rows)


def test_tasks_with_projects_avoids_n_plus_one(
    seeded: list[Project], django_assert_num_queries
) -> None:
    # Reading task.project.name in the loop must not trigger extra queries.
    with django_assert_num_queries(1):
        names = [task.project.name for task in tasks_with_projects()]
    assert len(names) == 12


def test_projects_with_prefetched_tasks_uses_two_queries(
    seeded: list[Project], django_assert_num_queries
) -> None:
    # One query for projects, one for the prefetched tasks; iterating the cache
    # adds nothing.
    with django_assert_num_queries(2):
        total = sum(len(list(project.tasks.all())) for project in projects_with_prefetched_tasks())
    assert total == 12


def test_high_priority_task_ids_is_bounded_and_filtered(seeded: list[Project]) -> None:
    project = seeded[0]
    Task.objects.create(project=project, title="urgent", priority=Task.Priority.CRITICAL)

    ids = high_priority_task_ids(str(project.id))

    assert all(isinstance(task_id, str) for task_id in ids)
    # Only the incomplete high/critical task qualifies.
    assert len(ids) == 1
