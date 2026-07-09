import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base for all domain models.

    Provides a UUID primary key (non-enumerable in the API), created/modified
    timestamps, and shared indexes/ordering. Subclasses must inherit
    ``BaseModel.Meta`` so these indexes and ordering are preserved.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["-created"]),
        ]
