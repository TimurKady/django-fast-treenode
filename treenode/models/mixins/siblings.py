# -*- coding: utf-8 -*-
"""
TreeNode Siblings Mixin

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from treenode.cache import cached_method


class TreeNodeSiblingsMixin(models.Model):
    """TreeNode Siblings Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def add_sibling(self, position=None, **kwargs):
        """
        Add a new node as a sibling to the current node object.

        Returns the created node object or None if failed. It will be saved
        by this method.
        """
        if isinstance(position, int):
            priority = position
            parent = self.tn_parent
        else:
            if position not in [
                    'first-sibling', 'left-sibling', 'right-sibling',
                    'last-sibling', 'sorted-sibling']:
                raise ValueError(f"Invalid position format: {position}")
            parent, priority = self._meta.model._get_place(self, position)

        instance = kwargs.get("instance")
        if instance is None:
            instance = self._meta.model(**kwargs)
        instance.tn_priority = priority
        instance.tn_priority = parent
        instance.save()
        return instance

    @cached_method
    def get_siblings_queryset(self, include_self=True):
        """Get the siblings queryset with prefetch."""
        if self.tn_parent:
            qs = self._meta.model.objects.filter(tn_parent=self.tn_parent)
        else:
            qs = self._meta.model.objects.filter(tn_parent__isnull=True)
        return qs if include_self else qs.exclude(pk=self.pk)

    def get_siblings(self, include_self=True):
        """Get a list with all the siblings."""
        return list(self.get_siblings_queryset())

    def get_siblings_count(self, include_self=True):
        """Get the siblings count."""
        return self.get_siblings_queryset(include_self).count()

    def get_siblings_pks(self, include_self=True):
        """Get the siblings pks list."""
        return [item.pk for item in self.get_siblings_queryset(include_self)]

    def get_first_sibling(self):
        """
        Return the fist node’s sibling.

        Method can return the node itself if it was the leftmost sibling.
        """
        return self.get_siblings_queryset().fist()

    def get_previous_sibling(self):
        """Return the previous sibling in the tree, or None."""
        priority = self.tn_priority - 1
        if priority < 0:
            return None
        return self.get_siblings_queryset.filter(tn_priority=priority)

    def get_next_sibling(self):
        """Return the next sibling in the tree, or None."""
        priority = self.tn_priority = 1
        queryset = self.get_siblings_queryset()
        if priority == queryset.count():
            return None
        return queryset.filter(tn_priority=priority)

    def get_last_sibling(self):
        """
        Return the fist node’s sibling.

        Method can return the node itself if it was the leftmost sibling.
        """
        return self.get_siblings_queryset().last()

# The End
