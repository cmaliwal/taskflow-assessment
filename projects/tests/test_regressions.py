"""Regression tests for the two defects documented in docs/task3-debugging-analysis.md.

Each test fails on the buggy implementation and passes on the fixed one.
"""

import pytest
from rest_framework.test import APIClient

from projects.models import Project, Task


@pytest.fixture
def project(db) -> Project:
    return Project.objects.create(name="Alpha", status=Project.Status.ACTIVE)


def test_priority_filter_with_valid_integer_returns_matches(
    api_client: APIClient, project: Project
) -> None:
    """Bug 1: priority is an IntegerField; a string icontains lookup 500s on PostgreSQL."""
    Task.objects.create(project=project, title="high", priority=Task.Priority.HIGH)
    Task.objects.create(project=project, title="low", priority=Task.Priority.LOW)

    response = api_client.get(f"/api/tasks/?priority={Task.Priority.HIGH}")

    assert response.status_code == 200
    titles = [task["title"] for task in response.json()["results"]]
    assert titles == ["high"]


def test_priority_filter_rejects_non_choice_value(api_client: APIClient, project: Project) -> None:
    """Bug 1: an out-of-range priority is a 400 (choice validation), not a 500."""
    response = api_client.get("/api/tasks/?priority=999")
    assert response.status_code == 400


def test_create_task_with_unknown_project_returns_400(api_client: APIClient, db) -> None:
    """Bug 2: an unknown FK id is rejected at validation (400), never a DB 500."""
    unknown_id = "00000000-0000-0000-0000-000000000000"
    payload = {"project": unknown_id, "title": "Orphan task", "priority": 2}

    response = api_client.post("/api/tasks/", payload, format="json")

    assert response.status_code == 400
    assert "project" in response.json()
