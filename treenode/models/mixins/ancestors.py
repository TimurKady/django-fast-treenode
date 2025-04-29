# -*- coding: utf-8 -*-
"""
TreeNode Ancestors Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from ...cache import cached_method


class TreeNodeAncestorsMixin(models.Model):
    """TreeNode Ancestors Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def get_ancestors_queryset(self, include_self=True):
        """Get all ancestors of a node."""
        pks = self.query("ancestors", include_self)
        return self._meta.model.objects.filter(pk__in=pks)

    @cached_method
    def get_ancestors_pks(self, include_self=True, depth=None):
        """Get the ancestors pks list."""
        return self.query("ancestors", include_self)

    @cached_method
    def get_ancestors(self, include_self=True):
        """Get a list of all ancestors of a node."""
        node = self if include_self else self.parent
        ancestors = []
        while node:
            ancestors.append(node)
            node = node.parent
        return ancestors[::-1]

    @cached_method
    def get_ancestors_count(self, include_self=True):
        """Get the ancestors count."""
        return self.query(
            objects="ancestors",
            include_self=include_self,
            mode='count'
        )

    def get_common_ancestor(self, target):
        """Find lowest common ancestor between self and other node."""
        if self._path == target._path:
            return self

        self_path_pks = self.query("ancestors")
        target_path_pks = target.query("ancestors")
        common = []

        for a, b in zip(self_path_pks, target_path_pks):
            if a == b:
                common.append(a)
            else:
                break

        if not common:
            return None

        ancestor_id = common[-1]
        return self._meta.model.objects.get(pk=ancestor_id)

# The End
