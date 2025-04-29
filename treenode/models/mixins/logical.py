# -*- coding: utf-8 -*-
"""
TreeNode Logical methods Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models


class TreeNodeLogicalMixin(models.Model):
    """TreeNode Logical Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def is_ancestor_of(self, target):
        """Check if self is an ancestor of other node."""
        return target.id in target.query("ancestors", include_self=False)

    def is_child_of(self, target):
        """Return True if the current node is child of target_obj."""
        return self._parent_id == target.id

    def is_descendant_of(self, target):
        """Check if self is a descendant of other node."""
        return target.id in target.query("descendants", include_self=False)

    def is_first_child(self):
        """Return True if the current node is the first child."""
        return self.priority == 0

    def has_children(self):
        """Return True if the node has children."""
        return self.query(objects="children", mode='exist')

    def is_last_child(self):
        """Return True if the current node is the last child."""
        siblings_pks = self.query("siblings", include_self=True)
        return siblings_pks[-1] == self.id

    def is_leaf(self):
        """Return True if the current node is a leaf."""
        return not self.has_children()

    def is_parent_of(self, target):
        """Return True if the current node is parent of target_obj."""
        return self.id == target._parent_id

    def is_root(self):
        """Return True if the current node is root."""
        return self.parent is None

    def is_root_of(self, target):
        """Return True if the current node is root of target_obj."""
        return self.pk == target.query("ancestors")[0]

    def is_sibling_of(self, target):
        """Return True if the current node is sibling of target_obj."""
        if target.parent is None and self.parent is None:
            # Both objects are roots
            return True
        return (self._parent_id == target._parent_id)


# The End
