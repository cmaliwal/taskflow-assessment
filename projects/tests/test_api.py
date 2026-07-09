import pytest
from rest_framework.test import APIClient

from projects.models import Project, Task


@pytest.fixture
def project(db) -> Project:
    return Project.objects.create(name="Alpha", status=Project.Status.ACTIVE)


@pytest.fixture
def tasks(project: Project) -> list[Task]:
    return [
        Task.objects.create(project=project, title="Design", priority=Task.Priority.HIGH),
        Task.objects.create(
            project=project,
            title="Build",
            priority=Task.Priority.LOW,
            is_complete=True,
        ),
        Task.objects.create(project=project, title="Ship", priority=Task.Priority.CRITICAL),
    ]


def test_create_project_returns_201(api_client: APIClient, db) -> None:
    response = api_client.post("/api/projects/", {"name": "New project"}, format="json")
    assert response.status_code == 201
    assert Project.objects.filter(name="New project").exists()


def test_create_project_blank_name_returns_400(api_client: APIClient) -> None:
    response = api_client.post("/api/projects/", {"name": "   "}, format="json")
    assert response.status_code == 400
    assert "name" in response.json()


def test_list_projects_is_paginated_with_task_count(
    api_client: APIClient, tasks: list[Task], project: Project
) -> None:
    response = api_client.get("/api/projects/")
    assert response.status_code == 200
    body = response.json()
    assert {"count", "next", "previous", "results"} <= set(body)
    result = next(item for item in body["results"] if item["id"] == str(project.id))
    assert result["task_count"] == 3


def test_retrieve_project_nests_tasks(
    api_client: APIClient, tasks: list[Task], project: Project
) -> None:
    response = api_client.get(f"/api/projects/{project.id}/")
    assert response.status_code == 200
    body = response.json()
    assert len(body["tasks"]) == 3
    assert body["tasks"][0]["priority_label"] in {"Low", "Medium", "High", "Critical"}


def test_create_task_returns_201(api_client: APIClient, project: Project) -> None:
    payload = {"project": str(project.id), "title": "Write docs", "priority": 2}
    response = api_client.post("/api/tasks/", payload, format="json")
    assert response.status_code == 201
    assert response.json()["priority_label"] == "Medium"


def test_update_task_marks_complete(api_client: APIClient, tasks: list[Task]) -> None:
    task = tasks[0]
    response = api_client.patch(f"/api/tasks/{task.id}/", {"is_complete": True}, format="json")
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.is_complete is True


def test_delete_task_returns_204(api_client: APIClient, tasks: list[Task]) -> None:
    task = tasks[0]
    response = api_client.delete(f"/api/tasks/{task.id}/")
    assert response.status_code == 204
    assert not Task.objects.filter(id=task.id).exists()


def test_filter_tasks_by_priority(api_client: APIClient, tasks: list[Task]) -> None:
    response = api_client.get(f"/api/tasks/?priority={Task.Priority.HIGH}")
    assert response.status_code == 200
    results = response.json()["results"]
    assert [t["title"] for t in results] == ["Design"]


def test_filter_tasks_by_is_complete(api_client: APIClient, tasks: list[Task]) -> None:
    response = api_client.get("/api/tasks/?is_complete=true")
    assert response.status_code == 200
    results = response.json()["results"]
    assert [t["title"] for t in results] == ["Build"]


def test_project_summary_counts_tasks(
    api_client: APIClient, tasks: list[Task], project: Project
) -> None:
    response = api_client.get(f"/api/projects/{project.id}/summary/")
    assert response.status_code == 200
    body = response.json()
    assert body["total_tasks"] == 3
    assert body["completed_tasks"] == 1
    assert body["completion_rate"] == 0.33


def test_project_summary_missing_project_returns_404(api_client: APIClient, db) -> None:
    response = api_client.get("/api/projects/00000000-0000-0000-0000-000000000000/summary/")
    assert response.status_code == 404
