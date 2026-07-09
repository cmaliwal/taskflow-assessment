# Taskflow - Pre-Implementation Architecture Plan
*Written in Cursor Plan Mode before any code, adapted from a production platform's conventions.*

## What I am building
A Django 5 + DRF + PostgreSQL REST API for project/task management, delivered
through a clean GitHub workflow: a minimal base on `main`, then one issue and one
PR per Section A task, each gated by CI (ruff + mypy + pytest).

## Decisions made BEFORE prompting

### 1. BaseModel with UUID primary key
All domain models extend `common.models.BaseModel`: UUID pk, `created`/`modified`
timestamps (indexed), shared `Meta` with ordering and indexes. UUID pks avoid
enumerable integer ids in the API and match the platform convention.

### 2. One model per file
`projects/models/project.py` and `projects/models/task.py`, re-exported from
`projects/models/__init__.py`. Better context isolation, fewer merge conflicts.

### 3. `priority` is IntegerChoices, not CharField
Numeric ordering is correct (1 < 2 < 3 < 4). Filtering uses `ChoiceFilter`, never
`CharFilter(icontains)`, which would raise a PostgreSQL DataError on an IntegerField.

### 4. Two serializers for Project
List = flat + annotated `task_count` (fast). Retrieve = nested prefetched tasks.
Switch via `get_serializer_class()`.

### 5. select_related vs prefetch_related
Task -> Project is a forward FK: `select_related` (JOIN). Project -> tasks is a
reverse FK: `prefetch_related`.

### 6. Summary endpoint is one annotated query
`Count("tasks")` + `Count("tasks", filter=Q(is_complete=True))` in a single query,
not two `.count()` calls.

### 7. transaction.atomic() in the seed command
Partial seeds leave the DB dirty. One transaction = all or nothing. bulk_create,
never `.save()` in a loop.

### 8. Structured LOGGING config
`logger.debug()` default, `logger.exception()` in except blocks, no print().

## GitHub delivery plan
- Base commit on `main`: rules, CI, scaffold, common/BaseModel, configs.
- Issue + branch + PR per Section A task (5 tasks). CI green, then squash-merge.

## CI plan
- `lint.yml`: ruff check, ruff format check, mypy (django-stubs).
- `unit_tests.yml`: pytest against a PostgreSQL service container, migrations applied.
