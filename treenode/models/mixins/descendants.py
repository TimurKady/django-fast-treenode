# -*- coding: utf-8 -*-
"""
TreeNode Descendants Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from django.db.models import OuterRef, Subquery, Min

from treenode.cache import treenode_cache, cached_method


class TreeNodeDescendantsMixin(models.Model):
    """TreeNode Descendants Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    @cached_method
    def get_descendants_queryset(self, include_self=False, depth=None):
        """Get the descendants queryset."""
        Closure = self.closure_model
        desc_qs = Closure.objects.filter(child=OuterRef('pk'), parent=self.pk)
        desc_qs = desc_qs.values('child').annotate(
            mdepth=Min('depth')).values('mdepth')[:1]

        queryset = self._meta.model.objects.annotate(
            min_depth=Subquery(desc_qs)
        ).filter(min_depth__isnull=False)

        if depth is not None:
            queryset = queryset.filter(min_depth__lte=depth)

        # add self if needed
        if include_self:
            queryset = queryset | self._meta.model.objects.filter(pk=self.pk)

        return queryset.order_by('min_depth', 'tn_priority')

    @cached_method
    def get_descendants_pks(self, include_self=False, depth=None):
        """Get the descendants pks list."""
        return self.get_descendants_queryset(include_self, depth)\
            .values_list("id", flat=True)

    def get_descendants(self, include_self=False, depth=None):
        """Get a list containing all descendants."""
        queryset = self.get_descendants_queryset(include_self, depth)
        return list(queryset)

    def get_descendants_count(self, include_self=False, depth=None):
        """Get the descendants count."""
        return len(self.get_descendants_pks(include_self, depth))

# The End
