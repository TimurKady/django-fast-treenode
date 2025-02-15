# -*- coding: utf-8 -*-
"""
TreeNode Proxy Model

This module defines an abstract base model `TreeNodeModel` that
implements hierarchical data storage using the Adjacency Table method.
It integrates with a Closure Table for optimized tree operations.

Features:
- Supports adjacency list representation with parent-child relationships.
- Integrates with a Closure Table for efficient ancestor and descendant
  queries.
- Provides a caching mechanism for performance optimization.
- Includes methods for tree traversal, manipulation, and serialization.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


# proxy.py

from django.db import models, transaction

from .factory import TreeFactory
from .classproperty import classproperty
from ..utils.base36 import to_base36
from ..managers import TreeNodeModelManager
from ..cache import cached_method, treenode_cache
import logging

logger = logging.getLogger(__name__)


class TreeNodeModel(models.Model, metaclass=TreeFactory):
    """
    Abstract TreeNode Model.

    Implements hierarchy storage using the Adjacency Table method.
    To increase performance, it has an additional attribute - a model
    that stores data from the Adjacency Table in the form of
    a Closure Table.
    """

    treenode_display_field = None
    closure_model = None

    tn_parent = models.ForeignKey(
        'self',
        related_name='tn_children',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    tn_priority = models.PositiveIntegerField(default=0)

    objects = TreeNodeModelManager()

    class Meta:
        """Meta Class."""

        abstract = True

    def __str__(self):
        """Display information about a class object."""
        if self.treenode_display_field:
            return str(getattr(self, self.treenode_display_field))
        else:
            return 'Node %d' % self.pk

    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------

    @classmethod
    def clear_cache(cls):
        """Clear cache for this model only."""
        treenode_cache.invalidate(cls._meta.label)

    @classmethod
    def get_closure_model(cls):
        """Return ClosureModel for class."""
        return cls.closure_model

    @classmethod
    def get_roots(cls):
        """Get a list with all root nodes."""
        qs = cls.get_roots_queryset()
        return list(item for item in qs)

    @classmethod
    @cached_method
    def get_roots_queryset(cls):
        """Get root nodes queryset with preloaded children."""
        qs = cls.objects.filter(tn_parent=None).prefetch_related('tn_children')
        return qs

    @classmethod
    def get_tree(cls, instance=None):
        """Get an n-dimensional dict representing the model tree."""
        objs_list = [instance] if instance else cls.get_roots()
        return [item._object2dict(item, []) for item in objs_list]

    @classmethod
    @cached_method
    def get_tree_display(cls):
        """Get a multiline string representing the model tree."""
        objs = list(cls.objects.all())
        return '\n'.join(['%s' % (obj,) for obj in objs])

    @classmethod
    @transaction.atomic
    def update_tree(cls):
        """Rebuilds the closure table."""
        # Clear cache
        cls.closure_model.delete_all()
        objs = list(cls.objects.all())
        cls.closure_model.objects.bulk_create(objs, batch_size=1000)
        cls.clear_cache()

    @classmethod
    def delete_tree(cls):
        """Delete the whole tree for the current node class."""
        cls.clear_cache()
        cls.objects.all().delete()
        cls.closure_model.delete_all()

    # Ancestors -------------------

    def get_ancestors_queryset(self, include_self=True, depth=None):
        """Get the ancestors queryset (ordered from parent to root)."""
        return self.closure_model.get_ancestors_queryset(
            self, include_self, depth)

    def get_ancestors(self, include_self=True, depth=None):
        """Get a list with all ancestors (ordered from root to self/parent)."""
        return list(
            self.get_ancestors_queryset(include_self, depth).iterator()
        )

    def get_ancestors_count(self, include_self=True, depth=None):
        """Get the ancestors count."""
        return self.get_ancestors_queryset(include_self, depth).count()

    def get_ancestors_pks(self, include_self=True, depth=None):
        """Get the ancestors pks list."""
        qs = self.get_ancestors_queryset(include_self, depth).only('pk')
        return [ch.pk for ch in qs] if qs else []

    # Children --------------------

    @cached_method
    def get_children_queryset(self):
        """Get the children queryset with prefetch."""
        return self.tn_children.prefetch_related('tn_children')

    def get_children(self):
        """Get a list containing all children."""
        return list(self.get_children_queryset().iterator())

    def get_children_count(self):
        """Get the children count."""
        return self.get_children_queryset().count()

    def get_children_pks(self):
        """Get the children pks list."""
        return [ch.pk for ch in self.get_children_queryset().only('pk')]

    # Descendants -----------------

    def get_descendants_queryset(self, include_self=False, depth=None):
        """Get the descendants queryset."""
        return self.closure_model.get_descendants_queryset(
            self, include_self, depth
        )

    def get_descendants(self, include_self=False, depth=None):
        """Get a list containing all descendants."""
        return list(
            self.get_descendants_queryset(include_self, depth).iterator()
        )

    def get_descendants_count(self, include_self=False, depth=None):
        """Get the descendants count."""
        return self.get_descendants_queryset(include_self, depth).count()

    def get_descendants_pks(self, include_self=False, depth=None):
        """Get the descendants pks list."""
        qs = self.get_descendants_queryset(include_self, depth)
        return [ch.pk for ch in qs] if qs else []

    # Siblings --------------------

    @cached_method
    def get_siblings_queryset(self):
        """Get the siblings queryset with prefetch."""
        if self.tn_parent:
            qs = self.tn_parent.tn_children.prefetch_related('tn_children')
        else:
            qs = self._meta.model.objects.filter(tn_parent__isnull=True)
        return qs.exclude(pk=self.pk)

    def get_siblings(self):
        """Get a list with all the siblings."""
        return list(self.get_siblings_queryset())

    def get_siblings_count(self):
        """Get the siblings count."""
        return self.get_siblings_queryset().count()

    def get_siblings_pks(self):
        """Get the siblings pks list."""
        return [item.pk for item in self.get_siblings_queryset()]

    # -----------------------------

    def get_breadcrumbs(self, attr=None):
        """Get the breadcrumbs to current node (self, included)."""
        return self.closure_model.get_breadcrumbs(self, attr)

    def get_depth(self):
        """Get the node depth (self, how many levels of descendants)."""
        return self.closure_model.get_depth(self)

    def get_first_child(self):
        """Get the first child node."""
        return self.get_children_queryset().first()

    @cached_method
    def get_index(self):
        """Get the node index (self, index in node.parent.children list)."""
        if self.tn_parent is None:
            return self.tn_priority
        source = list(self.tn_parent.tn_children.all())
        return source.index(self) if self in source else self.tn_priority

    def get_order(self):
        """Return the materialized path."""
        path = self.closure_model.get_breadcrumbs(self, attr='tn_priority')
        segments = [to_base36(i).rjust(6, '0') for i in path]
        return ''.join(segments)

    def get_last_child(self):
        """Get the last child node."""
        return self.get_children_queryset().last()

    def get_level(self):
        """Get the node level (self, starting from 1)."""
        return self.closure_model.get_level(self)

    def get_path(self, prefix='', suffix='', delimiter='.', format_str=''):
        """Return Materialized Path of node."""
        path = self.closure_model.get_path(self, delimiter, format_str)
        return prefix+path+suffix

    @cached_method
    def get_parent(self):
        """Get the parent node."""
        return self.tn_parent

    def set_parent(self, parent_obj):
        """Set the parent node."""
        self._meta.model.clear_cache()
        self.tn_parent = parent_obj
        self.save()

    def get_parent_pk(self):
        """Get the parent node pk."""
        return self.get_parent().pk if self.tn_parent else None

    @cached_method
    def get_priority(self):
        """Get the node priority."""
        return self.tn_priority

    def set_priority(self, priority=0):
        """Set the node priority."""
        self._meta.model.clear_cache()
        self.tn_priority = priority
        self.save()

    def get_root(self):
        """Get the root node for the current node."""
        return self.closure_model.get_root(self)

    def get_root_pk(self):
        """Get the root node pk for the current node."""
        root = self.get_root()
        return root.pk if root else None

    # Logics ----------------------

    def is_ancestor_of(self, target_obj):
        """Return True if the current node is ancestor of target_obj."""
        return self in target_obj.get_ancestors(include_self=False)

    def is_child_of(self, target_obj):
        """Return True if the current node is child of target_obj."""
        return self in target_obj.get_children()

    def is_descendant_of(self, target_obj):
        """Return True if the current node is descendant of target_obj."""
        return self in target_obj.get_descendants()

    def is_first_child(self):
        """Return True if the current node is the first child."""
        return self.tn_priority == 0

    def is_last_child(self):
        """Return True if the current node is the last child."""
        return self.tn_priority == self.get_siblings_count() - 1

    def is_leaf(self):
        """Return True if the current node is a leaf."""
        return self.tn_children.count() == 0

    def is_parent_of(self, target_obj):
        """Return True if the current node is parent of target_obj."""
        return self == target_obj.tn_parent

    def is_root(self):
        """Return True if the current node is root."""
        return self.tn_parent is None

    def is_root_of(self, target_obj):
        """Return True if the current node is root of target_obj."""
        return self == target_obj.get_root()

    def is_sibling_of(self, target_obj):
        """Return True if the current node is sibling of target_obj."""
        if target_obj.tn_parent is None and self.tn_parent is None:
            # Both objects are roots
            return True
        return (self.tn_parent == target_obj.tn_parent)

    def delete(self, cascade=True):
        """Delete node."""
        model = self._meta.model

        if not cascade:
            # Get a list of children
            children = self.get_children()
            # Move them to one level up
            for child in children:
                child.tn_parent = self.tn_parent
            # Udate both models in bulk
            model.objects.bulk_update(
                children,
                ("tn_parent",),
                batch_size=1000
            )
        # All descendants and related records in the ClosingModel will be
        # cleared by cascading the removal of ForeignKeys.
        super().delete()
        # Can be excluded. The cache has already been cleared by the manager.
        model.clear_cache()

    def save(self, force_insert=False, *args, **kwargs):
        """Save method."""
        # --- 1. Preparations -------------------------------------------------
        is_new = self.pk is None
        is_move = False
        old_parent = None
        old_priority = None
        model = self._meta.model
        closure_model = self.closure_model

        # --- 2. Check mode _-------------------------------------------------
        # If the object already exists in the DB, we'll extract its old parent
        if not is_new:
            ql = model.objects.filter(pk=self.pk).values_list(
                'tn_parent',
                'tn_priority').first()
            old_parent = ql[0]
            old_priority = ql[1]
            is_move = old_priority != self.tn_priority

        # Check if we are moving the node into itself (child).
        # If old parent != self.tn_parent, "moving" is possible.
        if old_parent and old_parent != self.tn_parent:
            # Let's make sure we don't move into our descendant
            descendants = self.get_descendants_queryset()
            if self.tn_parent and self.tn_parent.pk in {
                    d.pk for d in descendants}:
                raise ValueError("You cannot move a node into its own child.")

        # --- 3. Saving ------------------------------------------------------
        super().save(force_insert=force_insert, *args, **kwargs)

        # --- 4. Synchronization with Closure Model --------------------------
        if is_new:
            closure_model.insert_node(self)

        # If the parent has changed, we move it
        if (old_parent != self.tn_parent):
            closure_model.move_node(self)

        # --- 5. Update siblings ---------------------------------------------
        if is_new or is_move:
            # Now we need recalculate tn_priority
            self._update_priority()
        else:
            self._meta.model.clear_cache()

    # ---------------------------------------------------
    # Public properties
    #
    # All properties map a get_{{property}}() method.
    # ---------------------------------------------------

    @property
    def ancestors(self):
        """Get a list with all ancestors; self included."""
        return self.get_ancestors()

    @property
    def ancestors_count(self):
        """Get the ancestors count."""
        return self.get_ancestors_count()

    @property
    def ancestors_pks(self):
        """Get the ancestors pks list; self included."""
        return self.get_ancestors_pks()

    @property
    def breadcrumbs(self):
        """Get the breadcrumbs to current node (self, included)."""
        return self.get_breadcrumbs()

    @property
    def children(self):
        """Get a list containing all children; self included."""
        return self.get_children()

    @property
    def children_count(self):
        """Get the children count."""
        return self.get_children_count()

    @property
    def children_pks(self):
        """Get the children pks list."""
        return self.get_children_pks()

    @property
    def depth(self):
        """Get the node depth."""
        return self.get_depth()

    @property
    def descendants(self):
        """Get a list containing all descendants; self not included."""
        return self.get_descendants()

    @property
    def descendants_count(self):
        """Get the descendants count; self not included."""
        return self.get_descendants_count()

    @property
    def descendants_pks(self):
        """Get the descendants pks list; self not included."""
        return self.get_descendants_pks()

    @property
    def descendants_tree(self):
        """Get a n-dimensional dict representing the model tree."""
        return self.get_descendants_tree()

    @property
    def descendants_tree_display(self):
        """Get a multiline string representing the model tree."""
        return self.get_descendants_tree_display()

    @property
    def first_child(self):
        """Get the first child node."""
        return self.get_first_child()

    @property
    def index(self):
        """Get the node index."""
        return self.get_index()

    @property
    def last_child(self):
        """Get the last child node."""
        return self.get_last_child()

    @property
    def level(self):
        """Get the node level."""
        return self.get_level()

    @property
    def parent(self):
        """Get node parent."""
        return self.tn_parent

    @property
    def parent_pk(self):
        """Get node parent pk."""
        return self.get_parent_pk()

    @property
    def priority(self):
        """Get node priority."""
        return self.get_priority()

    @classproperty
    def roots(cls):
        """Get a list with all root nodes."""
        return cls.get_roots()

    @property
    def root(self):
        """Get the root node for the current node."""
        return self.get_root()

    @property
    def root_pk(self):
        """Get the root node pk for the current node."""
        return self.get_root_pk()

    @property
    def siblings(self):
        """Get a list with all the siblings."""
        return self.get_siblings()

    @property
    def siblings_count(self):
        """Get the siblings count."""
        return self.get_siblings_count()

    @property
    def siblings_pks(self):
        """Get the siblings pks list."""
        return self.get_siblings_pks()

    @classproperty
    def tree(cls):
        """Get an n-dimensional dict representing the model tree."""
        return cls.get_tree()

    @classproperty
    def tree_display(cls):
        """Get a multiline string representing the model tree."""
        return cls.get_tree_display()

    @property
    def tn_order(self):
        """Return the materialized path."""
        return self.get_order()

    # ---------------------------------------------------
    # Prived methods
    #
    # The usage of these methods is only allowed by developers. In future
    # versions, these methods may be changed or removed without any warning.
    # ---------------------------------------------------

    def _update_priority(self):
        """Update tn_priority field for siblings."""
        if self.tn_parent is None:
            # Node is a root
            parent = None
            queryset = self._meta.model.get_roots_queryset()
        else:
            # Node isn't a root
            parent = self.tn_parent
            queryset = parent.tn_children.all()

        siblings = list(queryset.exclude(pk=self.pk))
        sorted_siblings = sorted(siblings, key=lambda x: x.tn_priority)
        insert_pos = min(self.tn_priority, len(sorted_siblings))
        sorted_siblings.insert(insert_pos, self)
        for index, node in enumerate(sorted_siblings):
            node.tn_priority = index
        # Save changes
        model = self._meta.model
        with transaction.atomic():
            model.objects.bulk_update(sorted_siblings, ('tn_priority',), 1000)
        super().save(update_fields=['tn_priority'])
        model.clear_cache()

    def _object2dict(self, instance, exclude=None, visited=None):
        """
        Convert a class instance to a dictionary.

        :param instance: The object instance to convert.
        :param exclude: List of attribute names to exclude.
        :param visited: Set of visited objects to prevent circular references.
        :return: A dictionary representation of the object.
        """
        if exclude is None:
            exclude = set()
        if visited is None:
            visited = set()

        # Prevent infinite recursion by tracking visited objects
        if id(instance) in visited:
            raise RecursionError("Cycle detected in tree structure.")

        visited.add(id(instance))

        # Если объект не является моделью Django, просто вернуть его
        if not isinstance(instance, models.Model):
            return instance

        # If the object has no `__dict__`, return its direct value
        if not hasattr(instance, '__dict__'):
            return instance

        result = {}

        for key, value in vars(instance).items():
            if key.startswith('_') or key in exclude:
                continue

            # Recursively process nested objects
            if isinstance(value, (list, tuple, set)):
                result[key] = [
                    self._object2dict(v, exclude, visited) for v in value
                ]
            elif isinstance(value, dict):
                result[key] = {
                    k: self._object2dict(v, exclude, visited)
                    for k, v in value.items()
                }
            else:
                result[key] = self._object2dict(value, exclude, visited)

        # Include children
        children = instance.tn_children.all()
        if children.exists():
            result['children'] = [
                self._object2dict(child, exclude, visited)
                for child in children
            ]

        # Add path information
        result['path'] = instance.get_path(format_str=':d')

        return result


# The end
