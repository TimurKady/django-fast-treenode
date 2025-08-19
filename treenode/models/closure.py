"""

"""

from django.db import models
from .base import TreeNodeModel


class BaseClosureModel(models.Model):
    """."""

    parent = models.ForeignKey(
        'TreeNodeModel',
        related_name='children_set',
        on_delete=models.CASCADE,
    )

    child = models.ForeignKey(
        'TreeNodeModel',
        related_name='parents_set',
        on_delete=models.CASCADE,
    )

    depth = models.PositiveIntegerField()

    class Meta:
        """Meta Class."""

        abstract = True
        unique_together = (("parent", "child"),)
        indexes = [
            models.Index(fields=["parent", "child"]),
            models.Index(fields=["parent", "child", "depth"]),
        ]
