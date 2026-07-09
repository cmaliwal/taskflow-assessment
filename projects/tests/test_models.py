import uuid

import pytest

from projects.models import Project, Task


@pytest.fixture
def project(db) -> Project:
    return Project.objects.create(name="Alpha", status=Project.Status.ACTIVE)


def test_project_str_returns_name(project: Project) -> None:
    assert str(project) == "Alpha"


def test_project_status_defaults_to_active(db) -> None:
    created = Project.objects.create(name="Beta")
    assert created.status == Project.Status.ACTIVE


def test_project_uses_uuid_primary_key(project: Project) -> None:
    assert isinstance(project.id, uuid.UUID)


def test_task_is_accessible_via_project_related_name(project: Project) -> None:
    task = Task.objects.create(
        project=project,
        title="Write tests",
        priority=Task.Priority.HIGH,
    )
    assert str(task) == "Write tests"
    assert list(project.tasks.all()) == [task]


def test_task_priority_orders_numerically_not_alphabetically(project: Project) -> None:
    Task.objects.create(project=project, title="low", priority=Task.Priority.LOW)
    Task.objects.create(project=project, title="critical", priority=Task.Priority.CRITICAL)

    ordered = list(project.tasks.order_by("-priority").values_list("title", flat=True))

    assert ordered == ["critical", "low"]


def test_task_defaults_are_sensible(project: Project) -> None:
    task = Task.objects.create(project=project, title="Draft")
    assert task.priority == Task.Priority.MEDIUM
    assert task.is_complete is False
    assert task.assignee == ""
