# -*- coding: utf-8 -*-
"""
The TreeNode Model

This module defines an abstract base model `TreeNodeModel` that
implements hierarchical data storage using the Adjacency Table method.
It integrates with a Closure Table for optimized tree operations.

Features:
- Implements a basic tree representation as an Adjacency List with parent-child
  relationships.
- Combines the Adjacency List method with a Materialized Path for efficient
  ancestor and descendant queries.
- Provides a caching mechanism to optimize performance.
- Includes methods for tree traversal, manipulation, and serialization.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com

Причём с абсолютной поддержкой SQL-очередей, deferred execution,
кастомной сортировки и крутой архитектурой без лишнего дублирования.
"""

from __future__ import annotations

from collections import deque
from django.db import models, connection
from itertools import islice
from django.db.models.signals import pre_save, post_save
from django.utils.translation import gettext_lazy as _

from . import mixins as mx
from .factory import TreeNodeModelBase
from ..utils.db import ModelSQLService, SQLQueue
from ..managers import TreeNodeManager, TreeQueryManager, TreeTaskManager
from ..cache import treenode_cache as cache
from ..settings import SEGMENT_LENGTH, BASE
from ..signals import disable_signals


class TreeNodeModel(
        mx.TreeNodeAncestorsMixin, mx.TreeNodeChildrenMixin,
        mx.TreeNodeFamilyMixin, mx.TreeNodeDescendantsMixin,
        mx.TreeNodeLogicalMixin, mx.TreeNodeNodeMixin,
        mx.TreeNodePropertiesMixin, mx.TreeNodeRootsMixin,
        mx.TreeNodeSiblingsMixin, mx.TreeNodeTreeMixin, mx.RawSQLMixin,
        models.Model, metaclass=TreeNodeModelBase):
    """
    Abstract tree node model.

    Implements hierarchical storage using the adjacency table method.
    For performance improvements, it has additional Materialized Path
    attributes.
    """

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name=_('parent')
    )

    # Node order among siblings
    priority = models.PositiveIntegerField(
        default=0, verbose_name=_('priority')
    )

    # Node materialized path
    _path = models.TextField(default='', editable=False)
    # Maybe in the future, sometime...
    # _path_order = models.PositiveBigIntegerField(default=0, editable=False)
    # Node nesting depth
    _depth = models.PositiveIntegerField(default=0, editable=False)

    # Field for display in the Admin Class
    display_field = None

    class SortingChoices(models.TextChoices):
        """Sorting Direction Class."""

        ASC = "ASC", _("Ascending order")
        DESC = "DESC", _("Descending order")

    # Sorting field
    sorting_field = 'priority'
    # Sorting direction
    sorting_direction = SortingChoices.ASC
    # Model API protection flag via mandatory authorization via login
    api_login_required = False

    # Defaul manager
    objects = TreeNodeManager()
    # Task manager
    tasks = TreeTaskManager()
    # Query manager
    query = TreeQueryManager()

    # SQL Queue
    sqlq = SQLQueue()

    # DB Service
    db = ModelSQLService()

    class Meta:
        """Tree Meta Class."""

        indexes = [
            # models.Index(fields=["_path_order"]),
            models.Index(fields=["parent", "priority"]),
            models.Index(fields=["_depth", "priority"]),
        ]
        abstract = True

# -----------------------------------------------------------------
#
# General Methods
#
# -----------------------------------------------------------------

    def __str__(self):
        """Return a human-readable string representation of an object."""
        field = getattr(type(self), 'display_field', None)
        if field and hasattr(self, field):
            return str(getattr(self, field))
        return f'Node {self.pk}'

    def clear_cache(self):
        """Clear cache for this node only."""
        cache.invalidate(self._meta.label)

    # Generation methods ------------------------------------------

    def generate_path(self) -> str:
        """Build _path based on priorities of ancestors."""
        segment = f"{self.priority:0{SEGMENT_LENGTH}X}"
        return segment if self.parent is None else f"{self.parent._path}.{segment}"  # noqa: D501

    # Modification methods ----------------------------------------

    def delete(self, cascade=True):
        """Delete a node and clears the cache.

        If cascade=False, then:
        - If the node is not a root, its children are "lifted" to the parent,
        - If the node is a root (parent is None), its children become
          the new roots.
        """
        if not cascade:
            self.db.reassign_children(self.id, self.parent_id)

        # Delete the node itself
        super().delete()
        # Update subtree
        self._update_path(self.parent_id)
        self.sqlq.flush()
        # Clead cache
        self.clear_cache()

    # Saving and Udating methods ----------------------------------

    def save(self, *args, **kwargs):
        """
        Save or update the node.

        Method save() acts as a fast controller. All heavy-lifting is delegated
        to SQL queue. Queries are deterministic and ordered. Foelds of priority,
        _path, _depth are updated in one pass. Performance is close to maximum.
        """
        model = self._meta.model

        # Send signal pre_save
        pre_save.send(
            sender=model,
            instance=self,
            raw=False,
            using=self._state.db,
            update_fields=kwargs.get("update_fields", None)
        )

        # Routing
        is_new = False
        is_shift = False
        is_move = False

        if self.pk:
            state = self.get_db_state()
            if state:
                is_shift = self.priority != state["priority"]
                is_move = self.parent_id != state["parent_id"]
                if is_move:
                    self._meta.model.tasks.add("update", state["parent_id"])
            else:
                print("TreeNodeModel error: oject not found in DB! WTF, MF!")
        else:
            is_new = True

        # New node ----------------------------------
        if is_new:
            # Step 1. Set pk
            self.pk = self.db.get_next_id()

            # Step 2. Set priority
            if self.priority is None:
                self.priority = BASE - 1

            # Step 3. Set initial values
            self._path = self.generate_path()
            self._depth = self._path.count('.')

        """
        # Move node ---------------------------------
        elif is_move:
            # Reserved
            pass

        # Shift node --------------------------------
        elif is_shift:
            # Reserved
            pass

        else:
            # Reserved
            pass
        """

        if is_new or is_move or is_shift:
            # Step 1: Shift siblings
            if (is_new or is_move) and (self.priority is not None):
                self._shift_siblings_forward()
            # Step 2: Update paths for the new parent -> sqlq
            self._meta.model.tasks.add("update", self.parent_id)
            # Step 3: Clear model cache
            self.clear_cache()

        # Disable signals
        with (disable_signals(pre_save, model),
              disable_signals(post_save, model)):
            super().save(*args, **kwargs)

            if is_new or is_move or is_shift:
                # Run sql
                # self.sqlq.flush()
                setattr(model, 'is_dry', True)

        # Send signal post_save
        post_save.send(sender=model, instance=self, created=is_new)

        # Debug
        # self.check_tree_integrity()

    # Auxiliary methods -------------------------------------------

    def get_db_state(self):
        """Read paren and priority from DB."""
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT priority, parent_id FROM {self._meta.db_table} WHERE id = %s",  # noqa: D501
                [self.pk]
            )
            row = cursor.fetchone()
            if row:
                return {"priority": row[0], "parent_id": row[1]}
            return None

    # Maybe in the future, sometime...
    # def encode_path_order(self) -> int:
    #     """Encode path."""
    #     segments = self._path.split(".")
    #     value = 0
    #     for i, segment in enumerate(reversed(segments)):
    #         value += int(segment, 16) * (BASE ** i)
    #     return value

    # def decode_path_order(self) -> str:
    #     """Decode path."""
    #     segments = []
    #     path_order = self._path_order
    #     while path_order:
    #         path_order, rem = divmod(path_order, BASE)
    #         segments.insert(0, f"{rem:0{SEGMENT_LENGTH}X}")
    #     return ".".join(segments) if segments else "0" * SEGMENT_LENGTH

    @staticmethod
    def chunked(iterable, size):
        """Split an iterable into chunks of a given size."""
        it = iter(iterable)
        return iter(lambda: list(islice(it, size)), [])

    def check_tree_integrity(self, verbose: bool = True) -> list[str]:
        """
        Check tree consistency (_path, _depth and priority).

        Returns a list of errors (if any).
        :param verbose: If True - prints errors to console.
        How to use:
        root.check_tree_integrity()
        """
        model = self._meta.model
        errors = []
        queue = deque([self])

        while queue:
            node = queue.popleft()
            node.refresh_from_db()

            # Проверка _depth
            expected_depth = node._path.count(".")
            if node._depth != expected_depth:
                errors.append(
                    f"[DEPTH] id={node.pk} _depth={node._depth} ≠ path depth={expected_depth} / parent={node.parent_id}"  # noqa: D501
                )

            # Проверка generate_path
            expected_path = ".".join(
                f"{n.priority:0{SEGMENT_LENGTH}X}"
                for n in node.get_ancestors(include_self=True)
            )
            if node._path != expected_path:
                errors.append(
                    f"[PATH] id={node.pk} _path={node._path} ≠ expected={expected_path} / parent={node.parent_id}"  # noqa: D501
                )

            # Проверка уникальности priority среди сиблингов
            siblings = model.objects.filter(
                parent=node.parent).only("pk", "priority")
            priorities = [s.priority for s in siblings]
            if len(priorities) != len(set(priorities)):
                errors.append(
                    f"[PRIORITY] Duplicate priorities in siblings of id={node.pk} parent={node.parent_id}"  # noqa: D501
                )

            queue.extend(model.objects.filter(parent=node))

        if verbose and errors:
            print("Tree integrity check failed:")
            for err in errors:
                print("  -", err)
        elif verbose:
            print("Tree integrity: OK ✅")

        return errors

# ------------------------------------------------------------------
#
# Prived properties
#
# -----------------------------------------------------------------

    @property
    def _parent_id(self):
        """Lazy initialization of _parent_id."""
        if not hasattr(self, "_self_parent_id"):
            setattr(self, "_self_parent_id", self.parent_id)
        return self._self_parent_id

    @_parent_id.setter
    def _parent_id(self, value):
        """Setter for _parent_id."""
        setattr(self, "_self_parent_id", value)


# The End
