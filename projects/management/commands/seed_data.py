import logging
import random
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from faker import Faker

from projects.models import Project, Task

logger = logging.getLogger(__name__)
fake = Faker()


class Command(BaseCommand):
    help = "Seed the database with realistic projects and their tasks."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--projects",
            type=int,
            default=5,
            help="Number of projects to create (default: 5).",
        )
        parser.add_argument(
            "--tasks-per-project",
            type=int,
            default=8,
            help="Tasks to create per project (default: 8).",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        num_projects: int = options["projects"]
        tasks_per_project: int = options["tasks_per_project"]

        if num_projects < 1:
            raise CommandError("--projects must be at least 1.")
        if tasks_per_project < 0:
            raise CommandError("--tasks-per-project must not be negative.")

        statuses = list(Project.Status.values)
        priorities = list(Task.Priority.values)
        created_tasks = 0

        # transaction.atomic (decorator) ensures a failure leaves no partial seed.
        for _ in range(num_projects):
            project = Project.objects.create(
                name=fake.catch_phrase(),
                description=fake.paragraph(nb_sentences=3),
                status=random.choice(statuses),
            )
            tasks = [
                Task(
                    project=project,
                    title=fake.sentence(nb_words=4).rstrip("."),
                    assignee=fake.name(),
                    priority=random.choice(priorities),
                    due_date=fake.date_between(start_date="today", end_date="+30d"),
                    is_complete=fake.boolean(chance_of_getting_true=30),
                )
                for _ in range(tasks_per_project)
            ]
            # bulk_create: one INSERT for all of a project's tasks, never .save() in a loop.
            Task.objects.bulk_create(tasks)
            created_tasks += len(tasks)

        logger.debug("Seeded %s projects and %s tasks", num_projects, created_tasks)
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {num_projects} projects and {created_tasks} tasks.")
        )
