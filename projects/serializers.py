from rest_framework import serializers

from projects.models import Project, Task


class TaskSerializer(serializers.ModelSerializer):
    # queryset (not .none()) enables DRF's built-in FK existence validation:
    # an unknown project id is rejected with a 400, never a DB IntegrityError.
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "assignee",
            "priority",
            "priority_label",
            "due_date",
            "is_complete",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]

    def validate_title(self, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Title must not be blank.")
        return stripped


class TaskInlineSerializer(serializers.ModelSerializer):
    """Compact task representation nested inside a project detail response."""

    priority_label = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "priority", "priority_label", "is_complete", "due_date"]


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description", "status", "created", "modified"]
        read_only_fields = ["id", "created", "modified"]

    def validate_name(self, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("Name must not be blank.")
        qs = Project.objects.filter(name__iexact=stripped)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A project with this name already exists.")
        return stripped


class ProjectListSerializer(serializers.ModelSerializer):
    # Read from the _task_count annotation added by ProjectViewSet.get_queryset.
    task_count = serializers.IntegerField(source="_task_count", read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "status", "task_count", "created", "modified"]
        read_only_fields = fields


class ProjectDetailSerializer(serializers.ModelSerializer):
    tasks = TaskInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "status", "tasks", "created", "modified"]
        read_only_fields = ["id", "created", "modified"]
