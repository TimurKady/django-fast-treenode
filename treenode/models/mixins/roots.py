# -*- coding: utf-8 -*-
"""
TreeNode Roots Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from ...cache import cached_method


'''
try:
    profile
except NameError:
    def profile(func):
        """Profile."""
        return func
'''


class TreeNodeRootsMixin(models.Model):
    """TreeNode Roots Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    @classmethod
    def add_root(cls, position=None, **kwargs):
        """
        Add a root node to the tree.

        Adds a new root node at the specified position. If no position is
        specified, the new node will be the last element in the root.
        Parameters:
        position: can be 'first-root', 'last-root', 'sorted-root' or integer
        value.
        **kwargs – Object creation data that will be passed to the inherited
          Node model
        instance – Instead of passing object creation data, you can pass
          an already-constructed (but not yet saved) model instance to be
          inserted into the tree.

        Returns:
        The created node object. It will be save()d by this method.
        """
        if isinstance(position, int):
            priority = position
        else:
            if position not in ['first-root', 'last-root', 'sorted-root']:
                raise ValueError(f"Invalid position format: {position}")

            parent, priority = cls._get_place(None, position)

        instance = kwargs.get("instance")
        if instance is None:
            instance = cls(**kwargs)

        parent, priority = cls._get_place(None, position)
        instance.parent = None
        instance.priority = priority
        instance.save()
        return instance

    @classmethod
    def get_roots_queryset(cls):
        """Get root nodes queryset ordered according to model settings."""
        qs = cls.objects.filter(parent_id__isnull=True)
        ordering_fields = [
            "priority",
            "id",
        ] if cls.sorting_field == "priority" else [cls.sorting_field]
        prefix = "" if cls.sorting_direction == cls.SortingChoices.ASC else "-"
        order_args = [prefix + ordering_fields[0]] + ordering_fields[1:]
        return qs.order_by(*order_args)

    @classmethod
    def get_roots_pks(cls):
        """Get a list with all root nodes."""
        queryset = cls.get_roots_queryset()
        return queryset.values_list("id", flat=True)

    @classmethod
    @cached_method
    def get_roots(cls):
        """Get a list with all root nodes sorted properly."""
        return list(cls.get_roots_queryset())

    @classmethod
    def get_roots_count(cls):
        """Get a list with all root nodes."""
        return cls.get_roots_queryset().count()

    @classmethod
    def get_first_root(cls):
        """Return the first root node in the tree or None if it is empty."""
        roots = cls.get_roots_queryset()
        return roots.first()

    @classmethod
    def get_last_root(cls):
        """Return the last root node in the tree or None if it is empty."""
        roots = cls.get_roots_queryset()
        return roots.last()

    @classmethod
    def sort_roots(cls):
        """
        Re-sort root nodes.

        Sorts all nodes with parent_id IS NULL using a raw SQL query with
        a window function.
        The new ordering is computed based on the model's sorting_field
        (defaulting to 'priority').
        It updates the 'priority' field for all root nodes.
        """
        from django.db import connection

        db_table = cls._meta.db_table
        ordering_field = cls.sorting_field

        # Only root nodes have parent_id IS NULL
        where_clause = "parent_id IS NULL"
        params = []

        query = f"""
            WITH ranked AS (
                SELECT id,
                    ROW_NUMBER() OVER (ORDER BY {ordering_field}) - 1 AS new_priority
                FROM {db_table}
                WHERE {where_clause}
            )
            UPDATE {db_table} AS t
            SET priority = ranked.new_priority
            FROM ranked
            WHERE t.id = ranked.id;
        """

        with connection.cursor() as cursor:
            cursor.execute(query, params)


# The End
