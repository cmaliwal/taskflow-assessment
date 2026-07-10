# Taskflow Assessment

> **Section A - Python/Django Engineer Coding Assessment**
>
> A production-grade Django 5 + DRF + PostgreSQL REST API for managing projects and tasks.
> Built entirely using Cursor IDE with AI-assisted development, demonstrating not just working code,
> but a deliberate engineering workflow: issue tracking, CI/CD gating, automated code review, and
> the prompt engineering approach behind every decision.

**Repository:** https://github.com/cmaliwal/taskflow-assessment

---

## Why This Submission Stands Out

This is not just code that works. It demonstrates the **approach, process, and engineering judgment**
that separates senior-level AI-assisted development from junior copy-paste:

### 1. AI Code Review Bot (Gemini)

The single biggest risk with AI-generated code is **nobody reviews it critically**. I solved this
by building a Gemini-powered code review bot that runs on every pull request:

- Reviews every PR diff against the project's own `.cursor/rules/` (the rules I wrote)
- Posts structured feedback: Must fix / Should fix / Suggestions
- Blocks merging (REQUEST_CHANGES) on genuine violations
- Collapses previous review rounds automatically on re-push
- Demonstrates that I don't blindly trust AI output -- I built a system to catch my own mistakes

See: `.github/workflows/gemini_code_review.yml` and `.github/scripts/gemini_review.py`

### 2. Issue-Driven, PR-Gated Workflow

Every single piece of code arrived on `main` through the same loop:

```
Issue (acceptance criteria) -> Feature branch -> Code -> Local verify -> PR -> CI green -> Merge
```

- **21 issues** created and closed
- **21 PRs** squash-merged (no direct pushes to main, ever)
- **37 commits** with Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
- Full traceability: every PR references its issue, every merge closes it

This mirrors how a real team operates. The commit history tells a story.

### 3. Migration Safety (Production Incident Prevention)

Django migrations are a common source of deploy failures. I added three-layer protection:

- `check-migrations` -- fails if model changes lack a migration file
- `migration-up-to-date` -- blocks PRs with migrations from merging if they're behind `main` (prevents two PRs from creating duplicate migration numbers like `0009_a.py` and `0009_b.py`)
- `restage-migration-prs` -- when a migration lands on main, all other open migration PRs get their check re-triggered automatically

See: `.github/workflows/migrations.yml`

### 4. Rules-First AI Development

Before writing a single prompt, I encoded the engineering standards once:

- `.cursorrules` -- always-on golden rules and "never generate" list
- `.cursor/rules/` -- 9 domain-specific rule files (Django models, DRF, ORM, logging, testing, security, git workflow, Pythonic standards, database optimization)
- `.cursor/plans/taskflow-architecture.md` -- design decisions made before coding

The AI inherits these on every prompt. When I ask for "a filter for priority," the rules already forbid the `icontains`-on-IntegerField bug. This is the leverage of rules over prompts.

### 5. Complete CI/CD Pipeline (6 Workflows)

| Workflow | Purpose |
|----------|---------|
| `lint.yml` | ruff (lint + format) + mypy (strict type checking) |
| `unit_tests.yml` | pytest against a real PostgreSQL service (49 tests, 80%+ coverage) |
| `gemini_code_review.yml` | AI reviews every PR, blocks on must-fix findings |
| `migrations.yml` | Missing migration detection + duplicate number prevention |
| `release_notes.yml` | Auto-generates release notes for PRs into main |
| `pr_labeler.yml` | Auto-labels PRs by size (XS/S/M/L/XL) |

Plus: Dependabot for automated dependency updates, pre-commit hooks, issue templates, and a PR template.

---

## Assessment Task Completion (Section A)

| Task | What Was Delivered | Key Decisions |
|------|-------------------|---------------|
| **Task 1** - Project Scaffolding | Models (Project, Task), admin, migrations | UUID BaseModel, TextChoices for status, IntegerChoices for priority, annotated task_count in admin |
| **Task 2** - REST API | Full CRUD, filtering, pagination, `/summary/` | Separate list/detail/write serializers, ChoiceFilter (not CharFilter), single annotated query for summary |
| **Task 3** - Debug & Refactor | Documented both bugs, fixed, wrote regression tests | [docs/task3-debugging-analysis.md](./docs/task3-debugging-analysis.md) -- shows the buggy code, root cause, fix, and test |
| **Task 4** - DB Query & Performance | Annotate (task count + latest due date), select_related vs prefetch_related, bounded projections | All queries verified with `django_assert_num_queries` -- proven O(1) or O(2) regardless of data size |
| **Task 5** - Seed Command | `seed_data` with Faker, transaction.atomic, bulk_create | Configurable args, realistic data variety, error handling |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Framework | Django 5.x, Django REST Framework |
| Database | PostgreSQL 16 |
| Testing | pytest, pytest-django, pytest-cov, factory_boy |
| Linting | ruff (lint + format, including security rules) |
| Types | mypy with django-stubs (strict mode) |
| Docs | drf-spectacular (OpenAPI 3.0, Swagger UI, ReDoc) |
| Logging | Structured JSON (python-json-logger), Request ID middleware |
| CI/CD | GitHub Actions (6 workflows) |
| AI Review | Gemini 2.5 Flash via google-genai SDK |
| Secrets | detect-secrets pre-commit hook + GitHub Actions secrets |

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # edit DB credentials if needed
python manage.py migrate
python manage.py seed_data      # populate with realistic data
python manage.py runserver
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/api/ | API root (browsable) |
| http://localhost:8000/api/schema/swagger-ui/ | Swagger UI |
| http://localhost:8000/api/schema/redoc/ | ReDoc |
| http://localhost:8000/health/ | Health check |
| http://localhost:8000/ready/ | Readiness probe (DB connectivity) |
| http://localhost:8000/admin/ | Django Admin |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/projects/` | List (paginated, with `task_count`) / create |
| GET/PATCH/DELETE | `/api/projects/{id}/` | Retrieve (nested tasks) / update / delete |
| GET | `/api/projects/{id}/summary/` | Task totals, completion rate (single annotated query) |
| GET/POST | `/api/tasks/` | List / create |
| GET/PATCH/DELETE | `/api/tasks/{id}/` | Retrieve / update / delete |

**Filters:** `?priority=3`, `?is_complete=true`, `?project={id}`, `?status=active`
**Search:** `?search=keyword`
**Ordering:** `?ordering=-created`, `?ordering=priority`
**Pagination:** `?page=2` (page size: 20)

---

## Project Structure

```
taskflow/                   Django project config
  settings.py               Environment-driven, structured logging, DRF defaults
  urls.py                   Root URL config (admin, health, API, schema)

common/                     Shared building blocks
  models/base.py            BaseModel: UUID pk + created/modified + indexes
  exceptions.py             Custom DRF exception handler (consistent error shape)
  middleware.py             Request ID middleware (X-Request-ID propagation)
  views.py                  Health + readiness endpoints

projects/                   Domain app
  models/
    project.py              Project + ProjectQuerySet + ProjectManager
    task.py                 Task + TaskQuerySet + TaskManager
  serializers.py            List / detail / write serializers
  filters.py                ChoiceFilter for IntegerChoices/TextChoices
  views.py                  ViewSets with optimized querysets per action
  orm_examples.py           Documented ORM patterns with query bounds
  urls.py                   DRF DefaultRouter
  management/commands/      seed_data
  tests/                    49 tests (API, models, ORM, regressions, factories, seed)

.cursor/
  rules/                    9 domain-specific rule files (the AI's guardrails)
  plans/                    Architecture decisions (pre-implementation)

.github/
  workflows/                6 CI/CD workflows
  scripts/                  Gemini review + release notes Python scripts
  prompts/                  Review prompt (adapted from production codebase)
  ISSUE_TEMPLATE/           Bug report + feature request templates
  pull_request_template.md  PR template with checklist
  dependabot.yml            Automated dependency updates

docs/
  task3-debugging-analysis.md   Bug reproduction, root cause, fix methodology
```

---

## Development

```bash
make lint           # ruff check + ruff format --check
make types          # mypy strict
make test           # pytest with coverage
make all            # lint + types + test (what CI runs)
make format         # auto-format
make seed           # populate DB with realistic data
```

Or without Make:

```bash
ruff check . && ruff format --check .
mypy common projects taskflow
pytest --cov --cov-fail-under=80
```

---

## Engineering Decisions Worth Noting

| Decision | Why |
|----------|-----|
| UUID primary keys | Non-enumerable in API (security), no integer-guessing attacks |
| IntegerChoices for priority | Enables correct numeric filtering + natural ordering |
| TextChoices for status | Human-readable in API, validated at serializer edge |
| Separate list/detail/write serializers | List is fast (annotated count, no nesting); detail is rich (prefetched tasks); write validates input |
| Custom QuerySets + Managers | "The Model IS the service layer" -- no Service classes for CRUD |
| ChoiceFilter (not CharFilter) | CharFilter with icontains on an IntegerField causes PostgreSQL DataError -- this is Bug #1 from Task 3 |
| PrimaryKeyRelatedField with real queryset | .none() bypasses FK existence validation -- this is Bug #2 from Task 3 |
| django_assert_num_queries in tests | Proves query bounds mathematically, not by "it seems fast" |
| Custom exception handler | All errors return `{"errors": {...}}` -- never leaks model names, SQL, or paths |
| Structured JSON logging | Production-ready log format, Request ID correlation, configurable per-module |

---

## How This Was Built (AI Workflow)

See **[CURSOR_WORKFLOW.md](./CURSOR_WORKFLOW.md)** for the complete documentation:

- The Cursor rules configured before any code was written
- The exact prompt approach used per task
- Which Cursor mode was used (Plan / Agent / Ask)
- What `@context` references were passed
- What corrections were made after AI generation
- Why certain AI suggestions were rejected

This document is the real demonstration of **prompt engineering quality** (Task 5's rubric).

---

## Pull Request History (Chronological)

Every PR passed all CI checks (lint, types, tests, AI review, migrations) before merging:

| PR | Title | What it demonstrates |
|----|-------|---------------------|
| #13 | Task 1: Project and Task models with admin and migrations | Proper model design, admin optimization |
| #14 | Task 2: CRUD REST API with filtering, summary, and pagination | DRF best practices, single-query summary |
| #15 | Task 3: Reproduce and fix priority filter and FK validation defects | Debugging methodology, regression tests |
| #16 | Task 4: ORM optimization examples with query-bound tests | annotate, select_related, prefetch_related |
| #17 | Task 5: seed_data management command with realistic data | Prompt engineering, transaction safety |
| #19 | Docs: AI-assisted Cursor workflow and prompts | The workflow documentation |
| #21 | feat(ci): Gemini code review, release notes, PR size labeler | AI review bot, CI/CD automation |
| #29 | ci: Migration safety checks | Production incident prevention |
| #40-50 | Production hardening PRs | OpenAPI, coverage, factories, logging, security |

---

## What I Would Add Next (Given More Time)

- Authentication (JWT or session-based) with per-user data scoping
- Docker Compose for one-command local environment
- Celery for async task processing (email notifications on task completion)
- Database read replicas and connection pooling
- E2E API tests with a dedicated test environment
- GitHub branch protection rules requiring review bot approval

---

## Key Files to Review First

If you only have 5 minutes:

1. **[CURSOR_WORKFLOW.md](./CURSOR_WORKFLOW.md)** -- the prompt engineering and AI workflow documentation
2. **[.cursorrules](./.cursorrules)** -- the always-on AI guardrails
3. **[projects/views.py](./projects/views.py)** -- shows the ViewSet design with optimized querysets
4. **[projects/orm_examples.py](./projects/orm_examples.py)** -- documented ORM patterns with query bounds
5. **[docs/task3-debugging-analysis.md](./docs/task3-debugging-analysis.md)** -- the debugging methodology
6. **[.github/workflows/](./github/workflows/)** -- the full CI/CD pipeline
