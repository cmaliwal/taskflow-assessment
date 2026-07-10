import pytest

from projects.models import Project, Task
from projects.tests.factories import ProjectFactory, TaskFactory


@pytest.mark.django_db
def test_project_factory_creates_valid_project() -> None:
    project: Project = ProjectFactory()  # type: ignore[assignment]
    assert Project.objects.filter(pk=project.pk).exists()
    assert project.status == Project.Status.ACTIVE
    assert project.name.startswith("Project ")


@pytest.mark.django_db
def test_task_factory_creates_valid_task_with_project() -> None:
    task: Task = TaskFactory()  # type: ignore[assignment]
    assert Task.objects.filter(pk=task.pk).exists()
    assert task.project_id is not None
    assert task.priority == Task.Priority.MEDIUM
    assert task.is_complete is False


@pytest.mark.django_db
def test_task_factory_accepts_explicit_project() -> None:
    project: Project = ProjectFactory(name="Custom Project")  # type: ignore[assignment]
    task: Task = TaskFactory(project=project)  # type: ignore[assignment]
    assert task.project == project


@pytest.mark.django_db
def test_task_factory_names_are_unique() -> None:
    t1: Task = TaskFactory()  # type: ignore[assignment]
    t2: Task = TaskFactory()  # type: ignore[assignment]
    assert t1.title != t2.title


@pytest.mark.django_db
def test_project_factory_names_are_unique() -> None:
    p1: Project = ProjectFactory()  # type: ignore[assignment]
    p2: Project = ProjectFactory()  # type: ignore[assignment]
    assert p1.name != p2.name
