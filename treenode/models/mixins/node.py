# -*- coding: utf-8 -*-
"""
TreeNode Node Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models

from ...settings import BASE

try:
    profile
except NameError:
    def profile(func):
        """Profile."""
        return func


class TreeNodeNodeMixin(models.Model):
    """TreeNode Node Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def get_breadcrumbs(self, attr='id'):
        """Optimized breadcrumbs retrieval with direct cache check."""
        ancestors = self.get_ancestors()
        return [getattr(n, attr, None) for n in ancestors]

    def get_depth(self):
        """Get the node depth (self, how many levels of descendants)."""
        is_dry = getattr(self, "is_dry", True) or len(self.tasks.queue) > 0
        if is_dry:
            self.tasks.run()
            self.refresh()
        return self._depth

    def distance_to(self, targer):
        """Return number of edges on shortest path between two nodes."""
        self_path = self.query(objects='ancestors')
        targer_path = targer.query(objects='ancestors')

        i = 0
        for a, b in zip(self_path, targer_path):
            if a != b:
                break
            i += 1

        return (len(self_path) - i) + (len(targer_path) - i)

    def get_index(self):
        """Get the node index (self, index in node.parent.children list)."""
        return self.priority

    def get_level(self):
        """Get the node level (self, starting from 1)."""
        is_dry = getattr(self, "is_dry", True)
        if is_dry:
            self.refresh()
        return self._depth + 1

    def get_left(self):
        """Get the node to left."""
        return self.get_previous_sibling()

    def get_right(self):
        """Get the node to right."""
        return self.get_next_sibling()

    def get_order(self):
        """Return the materialized path."""
        is_dry = getattr(self, "is_dry", True) or len(self.tasks.queue) > 0
        if is_dry:
            self.tasks.run()
            self.refresh()
        return self._path

    def get_path(self, prefix='', suffix='', delimiter='.', format_str=''):
        """Return Materialized Path of node."""
        priorities = self.get_breadcrumbs(attr='priority')
        if not priorities or all(p is None for p in priorities):
            return prefix + suffix

        str_ = "{%s}" % format_str
        path = delimiter.join([
            str_.format(p)
            for p in priorities
            if p is not None
        ])
        return prefix + path + suffix

    @classmethod
    def shortest_path(cls, source, destination):
        """
        Return the shortest path (as list of PKs).

        Returned value is pks from `source` to `destination`, going up to their
        lowest common ancestor (LCA), then down to `destination`.
        """
        source_path = source.query(objects='ancestors')
        destination_path = destination.query(objects='ancestors')

        # Find the divergence index
        i = 0
        for a, b in zip(source_path, destination_path):
            if a != b:
                break
            i += 1

        # Path up from source to LCA (excluding LCA)
        up = source_path[:i-1:-1]
        # path down from LCA to destination (including LCA)
        down = destination_path[i-1:]

        return up + down

    def insert_at(self, target, position=None, save=False):
        """
        Insert a node into the tree relative to the target node.

        Parameters:
        target: еhe target node relative to which this node will be placed.
        position – the position, relative to the target node, where the
        current node object will be moved to, can be one of. Look _get_place().

        save : if `save=true`, the node will be saved in the tree. Otherwise,
        the method will return a model instance with updated fields: parent
        field and position in sibling list.

        Before using this method, the model instance must be correctly created
        with all required fields defined. If the model has required fields,
        then simply creating an object and calling insert_at() will not work,
        because Django will raise an exception.
        """
        # This method seems to have very dubious practical value.
        parent, priority = self._meta.model._get_place(target, position)
        self.parent = parent
        self.priority = priority

        if save:
            self.save()

    def move_to(self, target, position='last-child'):
        """
        Move node with subtree relative to target node and position.

        Parameters:
        target: еhe target node relative to which this node will be placed.
        position – the position, relative to the target node, where the
        current node object will be moved to, can be one of. Look _get_place().
        """
        parent, priority = self._meta.model._get_place(target, position)
        self.parent = parent
        self.priority = priority
        self.save()

    def get_parent(self):
        """Get the parent node."""
        return self.parent

    def set_parent(self, parent_obj):
        """Set the parent node."""
        self.parent = parent_obj
        self.save()

    def get_parent_pk(self):
        """Get the parent node pk."""
        return self._parent_id

    def get_priority(self):
        """Get the node priority."""
        return self.priority

    def set_priority(self, priority=0):
        """Set the node priority."""
        self.priority = priority
        self.save()

    def get_root(self):
        """Get the root node for the current node."""
        if self.parent_id is None:
            return self
        root_pk = self.query(objects='root')[0]
        return self._meta.model.objects.filter(pk=root_pk).first()

    def get_root_pk(self):
        """Get the root node pk for the current node."""
        return self.query(objects='root')

# -----------------------------------------------------------------

    @classmethod
    # @profile
    def _get_place(cls, target, position='last-child'):
        """
        Get position relative to the target node.

        position – the position, relative to the target node, where the
        current node object will be moved to, can be one of:

        - first-root: the node will be the first root node;
        - last-root: the node will be the last root node;
        - sorted-root: the new node will be moved after sorting by
          the treenode_sort_field field;

        - first-sibling: the node will be the new leftmost sibling of the
          target node;
        - left-sibling: the node will take the target node’s place, which will
          be moved to the target position with shifting follows nodes;
        - right-sibling: the node will be moved to the position after the
          target node;
        - last-sibling: the node will be the new rightmost sibling of the
          target node;
        - sorted-sibling: the new node will be moved after sorting by
          the treenode_sort_field field;

        - first-child: the node will be the first child of the target node;
        - last-child: the node will be the new rightmost child of the target
        - sorted-child: the new node will be moved after sorting by
          the treenode_sort_field field.

        """
        choices = {
            "first-root": lambda: (None, 0),
            "last-root": lambda: (None, BASE - 1),
            "sorted-root": lambda: (None, 0),

            "first-sibling": lambda: (target.parent, 0),
            "left-sibling": lambda: (target.parent, target.priority),
            "right-sibling": lambda: (target.parent, target.priority + 1),
            "last-sibling": lambda: (target.parent, BASE - 1),
            "sorted-sibling": lambda: (target.parent, 0),

            "first-child": lambda: (target, 0),
            "last-child": lambda: (target, BASE - 1),
            "sorted-child": lambda: (target, 0),
        }

        if isinstance(position, int):
            return target, position
        elif not isinstance(position, str) or position not in choices:
            raise ValueError(f"Invalid position format: {position}")

        return choices[position]()


# The End
