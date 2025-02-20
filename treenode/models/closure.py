# -*- coding: utf-8 -*-
"""
TreeNode Closure Model

This module defines the Closure Table implementation for hierarchical
data storage in the TreeNode model. It supports efficient queries for
retrieving ancestors, descendants, breadcrumbs, and tree depth.

Features:
- Uses a Closure Table for efficient tree operations.
- Implements cached queries for improved performance.
- Provides bulk operations for inserting, moving, and deleting nodes.

Version: 2.0.11
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import models, transaction

from ..managers import ClosureModelManager
from ..cache import cached_method, treenode_cache


class ClosureModel(models.Model):
    """
    Model for Closure Table.

    Implements hierarchy storage using the Closure Table method.
    """

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

    objects = ClosureModelManager()

    class Meta:
        """Meta Class."""

        abstract = True
        unique_together = (("parent", "child"),)
        indexes = [
            models.Index(fields=["parent", "child"]),
            models.Index(fields=["parent", "child", "depth"]),
        ]

    def __str__(self):
        """Display information about a class object."""
        return f"{self.parent} — {self.child} — {self.depth}"

    # ----------- Methods of working with tree structure ----------- #

    @classmethod
    def clear_cache(cls):
        """Clear cache for this model only."""
        treenode_cache.invalidate(cls._meta.label)

    @classmethod
    @cached_method
    def get_ancestors_pks(cls, node, include_self=True, depth=None):
        """Get the ancestors pks list."""
        options = dict(child_id=node.pk, depth__gte=0 if include_self else 1)
        if depth:
            options["depth__lte"] = depth
        queryset = cls.objects.filter(**options).order_by('depth')
        return list(queryset.values_list("parent_id", flat=True))

    @classmethod
    @cached_method
    def get_descendants_pks(cls, node, include_self=False, depth=None):
        """Get a list containing all descendants."""
        options = dict(parent_id=node.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})
        queryset = cls.objects.filter(**options)
        return list(queryset.values_list("child_id", flat=True))

    @classmethod
    @cached_method
    def get_root(cls, node):
        """Get the root node pk for the current node."""
        queryset = cls.objects.filter(child=node).order_by('-depth')
        return queryset.firts().parent if queryset.count() > 0 else None

    @classmethod
    @cached_method
    def get_depth(cls, node):
        """Get the node depth (how deep the node is in the tree)."""
        result = cls.objects.filter(child__pk=node.pk).aggregate(
            models.Max("depth")
        )["depth__max"]
        return result if result is not None else 0

    @classmethod
    @cached_method
    def get_level(cls, node):
        """Get the node level (starting from 1)."""
        return cls.objects.filter(child__pk=node.pk).aggregate(
            models.Max("depth"))["depth__max"] + 1

    @classmethod
    @transaction.atomic
    def insert_node(cls, node):
        """Add a node to a Closure table."""
        # Call bulk_create passing a single object
        cls.objects.bulk_create([node], batch_size=1000)
        # Clear cache
        cls.clear_cache()

    @classmethod
    @transaction.atomic
    def move_node(cls, nodes):
        """Move a nodes (node and its subtree) to a new parent."""
        # Call bulk_update passing a single object
        cls.objects.bulk_update(nodes, batch_size=1000)
        # Clear cache
        cls.clear_cache()

    @classmethod
    @transaction.atomic
    def delete_all(cls):
        """Clear the Closure Table."""
        # Clear cache
        cls.clear_cache()
        cls.objects.all().delete()

    def save(self, force_insert=False, *args, **kwargs):
        """Save method."""
        super().save(force_insert, *args, **kwargs)
        self._meta.model.clear_cache()

# The End
