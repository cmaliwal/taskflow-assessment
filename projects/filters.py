import django_filters

from projects.models import Project, Task


class TaskFilter(django_filters.FilterSet):
    # ChoiceFilter (not CharFilter with icontains): priority is an IntegerField,
    # so a string LIKE lookup would raise a PostgreSQL DataError. ChoiceFilter
    # validates against the enum and produces an exact integer match.
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)

    class Meta:
        model = Task
        fields = ["project", "priority", "is_complete"]


class ProjectFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Project.Status.choices)

    class Meta:
        model = Project
        fields = ["status"]
