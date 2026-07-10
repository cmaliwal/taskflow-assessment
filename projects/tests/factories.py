import factory
import factory.django

from projects.models import Project, Task


class ProjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating Project instances with sensible defaults."""

    name = factory.Sequence(lambda n: f"Project {n}")
    description = factory.Faker("sentence", nb_words=8)
    status = Project.Status.ACTIVE

    class Meta:
        model = Project


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating Task instances with sensible defaults.

    Usage::

        task = TaskFactory()                       # creates a project automatically
        task = TaskFactory(project=my_project)     # attach to an existing project
        task = TaskFactory(priority=Task.Priority.HIGH, is_complete=True)
    """

    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: f"Task {n}")
    assignee = factory.Faker("first_name")
    priority = Task.Priority.MEDIUM
    is_complete = False

    class Meta:
        model = Task
