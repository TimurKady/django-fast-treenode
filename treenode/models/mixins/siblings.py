# -*- coding: utf-8 -*-
"""
TreeNode Siblings Mixin

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
        instance = kwargs.get("instance")
        if instance is None:
            instance = self._meta.model(**kwargs)

        parent, priority = self._meta.model._get_place(self.patent, position)

        instance.parent = parent
        instance.priority = priority
        instance.save()
        if isinstance(position, str) and 'sorted' in position:
            self._sort_siblings()
        return instance

    def get_siblings_queryset(self, include_self=True):
        """Get Siblings QuerySet."""
        qs = self._meta.model.objects.filter(parent_id=self._parent_id)
        return qs if include_self else qs.exclude(pk=self.id)

    # @profile
    @cached_method
    def get_siblings(self, include_self=True):
        """Get a list with all the siblings."""
        queryset = self._meta.model.objects.filter(parent=self.parent)
        queryset = queryset if include_self else queryset.exclude(pk=self.pk)
        return [n for n in queryset]

    @cached_method
    def get_siblings_pks(self, include_self=True):
        """Get the siblings pks list."""
        return self.query("siblings", include_self)

    @cached_method
    def get_siblings_count(self):
        """Get the siblings count."""
        qs = self.query("siblings")
        return qs.count()

    @cached_method
    def get_first_sibling(self):
        """Return the first sibling in the tree, or None."""
        qs = self._meta.model.objects.filter(parent_id=self._parent_id)
        return qs.first()

    @cached_method
    def get_previous_sibling(self):
        """Return the previous sibling in the tree, or None."""
        options = {'parent_id': self._parent_id, 'priority__lt': self.priority}
        return self._meta.model.objects.filter(**options).last()

    def get_next_sibling(self):
        """Return the next sibling in the tree, or None."""
        options = {'parent_id': self._parent_id, 'priority__gt': self.priority}
        return self._meta.model.objects.filter(**options).first()

    def get_last_sibling(self):
        """
        Return the fist node’s sibling.

        Method can return the node itself if it was the leftmost sibling.
        """
        qs = self._meta.model.objects.filter(parent_id=self._parent_id)
        return qs.last()

# The End