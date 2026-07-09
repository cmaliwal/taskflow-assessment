# Cursor Workflow - How This Project Was Built

This document is the real deliverable behind the code. The brief is a test of
approach and prompt quality, not just whether the API works. So this captures
the complete AI-assisted workflow: the rules configured in Cursor before any
code was written, the exact prompts used per task, which mode was active, what
context was passed with @-references, and what I verified or corrected after
each generation.

## Philosophy: configure the AI before you prompt it

The single highest-leverage move in AI-assisted development is not writing
clever prompts. It is encoding the standards and constraints once, so every
prompt inherits them. Before generating a single model, I wrote:

- `.cursorrules` - the always-on summary of golden rules and a "never generate"
  list (no `print()`, no `.save()` in loops, no `CharFilter(icontains)` on a
  numeric field, no `PrimaryKeyRelatedField(queryset=...none())`).
- `.cursor/rules/*.mdc` - focused, path-scoped rules for logging, Pythonic code,
  Django models, Django admin, DRF, database optimization, testing, security,
  and git workflow. These are adapted from the conventions of a production
  platform codebase.
- `.cursor/plans/taskflow-architecture.md` - the design decisions I made in Plan
  Mode before prompting (UUID BaseModel, IntegerChoices for priority, list vs
  detail serializers, single-query summary, and so on).

With that in place, prompts can stay short because the rules do the heavy
lifting. When I ask for "a filter for priority," the rules already forbid the
buggy `icontains`-on-IntegerField pattern.

## Delivery workflow: issue, branch, PR, CI, merge

Every Section A task follows the same loop, mirroring how a senior engineer
ships on a real team:

1. Open a GitHub issue describing the task and acceptance criteria.
2. Create a feature branch named after the issue.
3. Generate the code in Cursor, guided by the rules.
4. Verify locally: `ruff check`, `ruff format --check`, `mypy`, `pytest`.
5. Open a PR that closes the issue.
6. Let CI (lint + type-check + tests on a PostgreSQL service) go green.
7. Squash-merge into `main`.

`main` began as a minimal base (rules + CI + scaffold + BaseModel). No task code
was ever pushed directly to `main`; it all arrived through reviewed PRs.

## The prompts, task by task

Below, each task shows the mode, the @-context, the prompt intent, and the
verification and corrections that followed. Prompts are paraphrased to their
operative content.

### Base: repository foundation

- Mode: Agent, after a Plan Mode discussion of structure.
- Context: `@.cursor/rules` `@.cursor/plans/taskflow-architecture.md`
- Prompt: "Scaffold a Django 5 + DRF project with env-based settings and
  structured LOGGING (debug default, exception in except blocks). Add
  `common.models.BaseModel` with a UUID pk and created/modified timestamps and
  indexes. Add a health check endpoint and its test. Add ruff + mypy config,
  pytest.ini, pre-commit, and GitHub Actions for lint and tests against a
  PostgreSQL service."
- Verified: `ruff`, `mypy`, `python manage.py check`, and the health test all
  green before the first push.

### Task 1 - Models (issue #1)

- Mode: Agent.
- Context: `@.cursor/rules/django/django-models-best-practices.mdc`
  `@common/models/base.py`
- Prompt: "Add `Project` (TextChoices status) and `Task` (IntegerChoices
  priority, project FK with related_name tasks, assignee, due_date,
  is_complete). One model per file under `projects/models/`, both extending
  BaseModel and inheriting BaseModel.Meta. Add composite indexes for the common
  filter paths. Register both in admin with annotated task counts, raw_id_fields,
  and date_hierarchy instead of timestamp list_filter. Generate the migration
  and model tests."
- Correction: the admin `task_count` display reads an annotated attribute; I
  annotated `get_queryset` and added a scoped `# type: ignore[attr-defined]` so
  mypy stays honest without silencing real errors.

### Task 2 - CRUD API (issue #3)

- Mode: Agent.
- Context: `@.cursor/rules/drf/drf-api-design.mdc` `@projects/models`
- Prompt: "Build ProjectViewSet and TaskViewSet on a DefaultRouter. Use list,
  detail, and write serializers; list annotates task_count, detail nests
  prefetched tasks, the task FK validates existence. Filter tasks by project,
  priority (ChoiceFilter, not CharFilter), and is_complete. Add a summary
  action that returns totals in a single annotated query. select_related on
  tasks, prefetch_related on project detail. Tests for CRUD, filtering, summary,
  pagination."
- Corrections found by verification:
  - mypy flagged `Project.objects.filter(pk=pk)` because the action `pk` is
    `str | None`; I added an explicit `None` guard that also returns a clean 404.
  - One create test did not request the `db` fixture, so pytest-django blocked
    DB access. Added `db`.

### Task 3 - Debugging (issue #9)

- Mode: Agent, framed as reconstruction since no buggy code was supplied.
- Context: `@projects/filters.py` `@projects/serializers.py`
- Prompt: "The brief mentions recruiter-supplied buggy code that never arrived.
  Reconstruct the two defects this kind of API usually ships with (priority
  filtered as text on an IntegerField, and an FK serializer bound to an empty
  queryset), write a root-cause analysis with buggy vs fixed code, and add
  regression tests that fail on the buggy version and pass on the current one."
- Verified: the three regression tests pass against the correct implementation.

### Task 4 - ORM optimization (issue #10)

- Mode: Agent.
- Context: `@.cursor/rules/database/database-optimization.mdc` `@projects/models`
- Prompt: "Add an orm_examples module: annotate-based aggregation replacing an
  N+1 count loop, select_related for the forward FK, prefetch_related for the
  reverse FK, and a bounded values_list projection. Document each function's
  query bounds. Add tests that assert the bounds with
  django_assert_num_queries."
- Correction: mypy cannot resolve annotation names inside `.values()`
  (a django-stubs limitation); scoped the ignore to that single line.

### Task 5 - Seed command (issue #11)

- Mode: Agent.
- Context: `@.cursor/rules/database/database-optimization.mdc`
- Prompt: "Add a seed_data management command: configurable --projects and
  --tasks-per-project, Faker for realistic values, transaction.atomic, and
  bulk_create for tasks. Output via self.stdout styles, never print(). Tests via
  call_command asserting counts, defaults, and validation."
- Verified: counts and validation assertions pass; `python manage.py seed_data`
  produces realistic data.

## What the AI got wrong (and why that is the point)

Generated code is a draft, not a deliverable. The corrections above (the `pk`
narrowing, the missing `db` fixture, the two `.values()`/annotation type
limitations) are exactly the places where judgment matters. The rules prevented
the big, silent mistakes; local verification caught the small ones before they
reached CI. Every fix was made once, and where a limitation was structural, the
`# type: ignore` was scoped narrowly rather than blanket-disabled.

## Reproducing the verification

```bash
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
mypy common projects taskflow
pytest
```
