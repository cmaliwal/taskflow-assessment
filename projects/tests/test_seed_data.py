from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from projects.models import Project, Task


def test_seed_data_creates_requested_counts(db) -> None:
    out = StringIO()
    call_command("seed_data", "--projects", "3", "--tasks-per-project", "4", stdout=out)

    assert Project.objects.count() == 3
    assert Task.objects.count() == 12
    assert "Seeded 3 projects and 12 tasks." in out.getvalue()


def test_seed_data_uses_defaults(db) -> None:
    call_command("seed_data")

    assert Project.objects.count() == 5
    assert Task.objects.count() == 40


def test_seed_data_rejects_invalid_project_count(db) -> None:
    with pytest.raises(CommandError):
        call_command("seed_data", "--projects", "0")


def test_seed_data_assigns_valid_choices(db) -> None:
    call_command("seed_data", "--projects", "2", "--tasks-per-project", "3")

    valid_statuses = set(Project.Status.values)
    valid_priorities = set(Task.Priority.values)
    assert all(p.status in valid_statuses for p in Project.objects.all())
    assert all(t.priority in valid_priorities for t in Task.objects.all())
