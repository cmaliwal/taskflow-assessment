# Taskflow

A Django 5 + Django REST Framework + PostgreSQL API for managing projects and
their tasks. Built AI-assisted with Cursor, following senior engineering
conventions (typed, linted, tested, documented) adapted from a production
platform codebase.

## Stack

- Python 3.12, Django 5.x, Django REST Framework
- PostgreSQL 16
- pytest + pytest-django (tests), ruff (lint + format), mypy (types)
- GitHub Actions CI: lint, type-check, and unit tests on every PR

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # edit DB credentials if needed
python manage.py migrate
python manage.py runserver
```

- API root: `http://localhost:8000/api/`
- Health check: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`

Seed realistic data:

```bash
python manage.py seed_data --projects 5 --tasks-per-project 8
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/projects/` | List (paginated, with `task_count`) / create |
| GET/PATCH/DELETE | `/api/projects/{id}/` | Retrieve (nested tasks) / update / delete |
| GET | `/api/projects/{id}/summary/` | Task totals and completion rate (single query) |
| GET/POST | `/api/tasks/` | List / create |
| GET/PATCH/DELETE | `/api/tasks/{id}/` | Retrieve / update / delete |

Query params: `?priority=3`, `?is_complete=true`, `?project={id}`, `?search=`,
`?ordering=-created`, `?page=2`.

## Delivery Workflow

`main` started as a minimal base (Cursor rules, CI, scaffold, `BaseModel`).
Each Section A task was delivered through its own GitHub issue, feature branch,
and pull request, gated by CI (ruff, mypy, pytest on a PostgreSQL service) and
squash-merged. No task code was pushed directly to `main`.

## Development

```bash
ruff check .            # lint
ruff format .           # format
mypy common projects taskflow   # type check
pytest                  # run the test suite (needs PostgreSQL)
pre-commit install      # enable git hooks
```

## Project Structure

```
taskflow/            Django project config (settings with structured LOGGING, urls)
common/              Shared building blocks
  models/base.py     BaseModel: UUID pk + created/modified timestamps + indexes
  views.py           Health check endpoint
projects/            Domain app
  models/            One model per file (Project, Task), re-exported
  serializers.py     DRF serializers with explicit validation
  filters.py         django-filter FilterSets (correct field types)
  views.py           ViewSets, custom actions, optimized querysets
  urls.py            DRF router
  management/commands/seed_data.py
  tests/             pytest suite
.cursor/             Cursor rules and architecture plan (the AI configuration)
.github/             CI workflows, issue/PR templates, dependabot
```

## How This Was Built

See [CURSOR_WORKFLOW.md](./CURSOR_WORKFLOW.md) for the full AI-assisted workflow:
the Cursor rules configured up front, the prompts used per task, and the
issue-to-PR-to-CI delivery process.
