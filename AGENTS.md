# AGENTS.md

Cross-agent instruction file for the Taskflow project. Applies to Cursor, Claude
Code, GitHub Copilot, and any other coding agent that reads this file. Detailed,
path-scoped rules live in `.cursor/rules/`. This file is the concise entry point.

## What this project is

A Django 5 + Django REST Framework + PostgreSQL REST API for managing projects
and their tasks. Python 3.12+. Typed (mypy), linted (ruff), tested (pytest).

## Key commands

```bash
ruff check .                        # lint
ruff format --check .               # format check
mypy common projects taskflow       # type check
pytest                              # run the full test suite
python manage.py seed_data          # populate the DB with realistic data
```

## Architecture

- All domain models extend `common.models.BaseModel` (UUID pk, `created`/`modified` timestamps, indexes).
- One model per file under `projects/models/`, re-exported from `projects/models/__init__.py`.
- `IntegerChoices` for ordered enumerations (priority); `TextChoices` for status.
- `ChoiceFilter` for `IntegerChoices`/`TextChoices` fields - never `CharFilter(icontains)` on a numeric field.
- `PrimaryKeyRelatedField(queryset=Model.objects.all())` always - never `.none()`.
- `select_related` for forward FK (one related object); `prefetch_related` for reverse FK / M2M.
- Separate list, detail, and write serializers; switch via `get_serializer_class()`.
- Annotate aggregates at the queryset level - never count in Python loops.
- `bulk_create()` for batch writes - never `.save()` in a loop.
- `transaction.atomic` for any batch operation that must be all-or-nothing.
- Validate at the serializer edge; bad input returns a clean 400, never a DB 500.
- Error messages must not leak model names, ORM details, SQL, or file paths.

## Logging

- Default to `logger.debug()`. Use `logger.info()` only for key production events.
- Inside `except` blocks always use `logger.exception()` - never `logger.error()`.
- Never use `print()` in application code.

## Testing

- pytest + pytest-django only. No `unittest.TestCase`.
- Test naming: `test_<subject>_<condition>_<expected_outcome>`.
- Every endpoint needs tests for the happy path, 404, validation errors, and filter correctness.
- Every bug fix ships with a regression test.

## Never generate

- `print()` in application code
- `.save()` inside loops
- `CharFilter(lookup_expr="icontains")` on a numeric field
- `PrimaryKeyRelatedField(queryset=Model.objects.none())`
- Bare `except:` clauses
- `logger.error()` inside an `except` block
- Hard-coded secrets or credentials
