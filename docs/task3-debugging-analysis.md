# Task 3 - Debugging Analysis

The client's brief describes a debugging exercise where a recruiter supplies
buggy code. No code was supplied, so this document reproduces the two defects
that this class of Django/DRF API almost always ships with, explains the root
cause of each, and links to the regression tests that lock in the fix.

Both defects are guarded by `projects/tests/test_regressions.py`. Run:

```bash
pytest projects/tests/test_regressions.py -v
```

---

## Bug 1: Filtering an IntegerField with a string `icontains` lookup

### Buggy code

```python
# projects/filters.py (buggy)
class TaskFilter(django_filters.FilterSet):
    # priority is a PositiveSmallIntegerField, but this treats it as text
    priority = django_filters.CharFilter(field_name="priority", lookup_expr="icontains")

    class Meta:
        model = Task
        fields = ["project", "priority", "is_complete"]
```

### Symptom

`GET /api/tasks/?priority=2` returns HTTP 500. PostgreSQL logs:

```
django.db.utils.DataError: operator does not exist: integer ~~* unknown
```

### Root cause

`icontains` compiles to a SQL `ILIKE` (`~~*`) comparison, which is only valid
for text columns. `priority` is an integer column, so PostgreSQL refuses the
operator and raises `DataError`. SQLite silently coerces and hides the bug in
local development, which is why it often reaches production unnoticed.

### Fix

Use `ChoiceFilter` bound to the model's `IntegerChoices`. This validates the
input against the allowed enum values and produces an exact integer match.

```python
# projects/filters.py (fixed - current implementation)
class TaskFilter(django_filters.FilterSet):
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)

    class Meta:
        model = Task
        fields = ["project", "priority", "is_complete"]
```

### Regression tests

- `test_priority_filter_with_valid_integer_returns_matches` - the request that
  used to 500 now returns 200 with only matching tasks.
- `test_priority_filter_rejects_non_choice_value` - an out-of-range priority is
  rejected with 400 instead of leaking a database error.

---

## Bug 2: Serializer FK declared with an empty queryset

### Buggy code

```python
# projects/serializers.py (buggy)
class TaskSerializer(serializers.ModelSerializer):
    # empty queryset disables DRF's existence check
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.none())
```

### Symptom

`POST /api/tasks/` with a `project` id that does not exist returns HTTP 500
with an `IntegrityError` (foreign key violation) instead of a clean validation
error.

### Root cause

`PrimaryKeyRelatedField` uses its `queryset` to verify that the referenced
object exists during validation. An empty queryset (`.none()`) means every
lookup fails to match but the field is still accepted as "valid" input in some
configurations, or the id is passed straight through to the database, which
then rejects the insert with an `IntegrityError`. Either way the client gets a
500 for what is really a 400-level input error, and the error message can leak
internal details.

### Fix

Bind the field to the real queryset so DRF validates existence before the write.

```python
# projects/serializers.py (fixed - current implementation)
class TaskSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
```

### Regression test

- `test_create_task_with_unknown_project_returns_400` - posting an unknown
  project id now returns 400 with a `project` field error, never a 500.

---

## Debugging method used

1. Reproduce the failure with the smallest possible request.
2. Read the actual database error, not just the 500 page.
3. Identify the layer that should have caught the bad input (filter/serializer),
   not the layer that happened to raise (database).
4. Fix at the correct layer and add a regression test that fails on the old code
   and passes on the new code.
