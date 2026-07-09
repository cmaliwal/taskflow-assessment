from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from projects.models import Project, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "task_count", "created")
    list_filter = ("status",)
    search_fields = ("name", "description")
    date_hierarchy = "created"
    readonly_fields = ("id", "created", "modified")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Project]:
        return super().get_queryset(request).annotate(_task_count=Count("tasks"))

    @admin.display(description="Tasks", ordering="_task_count")
    def task_count(self, obj: Project) -> int:
        # _task_count is annotated in get_queryset above.
        return obj._task_count  # type: ignore[attr-defined]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "priority", "is_complete", "due_date", "created")
    list_filter = ("priority", "is_complete")
    search_fields = ("title", "assignee")
    raw_id_fields = ("project",)
    list_select_related = ("project",)
    date_hierarchy = "created"
    readonly_fields = ("id", "created", "modified")
