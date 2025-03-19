# -*- coding: utf-8 -*-
"""
TreeNode Ancestors Mixin

Version: 2.1.4
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from django.db.models import OuterRef, Subquery, IntegerField, Case, When, Value
from ...cache import treenode_cache, cached_method


class TreeNodeAncestorsMixin(models.Model):
    """TreeNode Ancestors Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    @cached_method
    def get_ancestors_queryset(self, include_self=True, depth=None):
        """Get the ancestors queryset (ordered from root to parent)."""
        options = dict(child_id=self.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})

        return self.closure_model.objects\
            .filter(**options)\
            .order_by('-depth')

    @cached_method
    def get_ancestors_pks(self, include_self=True, depth=None):
        """Get the ancestors pks list."""
        return self.get_ancestors_queryset(include_self, depth)\
            .values_list('id', flat=True)

    def get_ancestors(self, include_self=True, depth=None):
        """Get a list with all ancestors (ordered from root to self/parent)."""
        return list(self.get_ancestors_queryset(include_self, depth))

    def get_ancestors_count(self, include_self=True, depth=None):
        """Get the ancestors count."""
        return len(self.get_ancestors_pks(include_self, depth))

# The End
