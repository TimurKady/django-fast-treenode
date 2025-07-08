# -*- coding: utf-8 -*-
"""
TreeNode Children Mixin

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


class TreeNodeChildrenMixin(models.Model):
    """TreeNode Ancestors Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def add_child(self, position=None, **kwargs):
        """
        Add a child to the node.

        position:
        Can be 'first-child', 'last-child', 'sorted-child' or integer value.

        Parameters:
        **kwargs – Object creation data that will be passed to the inherited
          Node model
        instance – Instead of passing object creation data, you can pass
          an already-constructed (but not yet saved) model instance to be
          inserted into the tree.

        Returns:
        The created node object. It will be save()d by this method.
        """
        instance = kwargs.get("instance")
        if instance is None:
            instance = self._meta.model(**kwargs)

        parent, priority = self._meta.model._get_place(self, position)

        instance.parent = self
        instance.priority = priority
        instance.save()

    def get_children_queryset(self):
        """Get the children queryset sorted according to model settings."""
        cls = self._meta.model
        qs = cls.objects.filter(parent_id=self.id)
        ordering_fields = [
            "priority",
            "id",
        ] if cls.sorting_field == "priority" else [cls.sorting_field]
        prefix = "" if cls.sorting_direction == cls.SortingChoices.ASC else "-"
        order_args = [prefix + ordering_fields[0]] + ordering_fields[1:]
        return qs.order_by(*order_args)

    @cached_method
    def get_children(self):
        """Get a list containing all children sorted properly."""
        queryset = self.get_children_queryset()
        return list(queryset)

    @cached_method
    def get_children_pks(self):
        """Get the children pks list."""
        return self.query("children")

    @cached_method
    def get_children_count(self):
        """Get the children count."""
        return self.query(objects="children", mode='count')

    @cached_method
    def get_first_child(self):
        """Get the first child node or None if it has no children."""
        return self.get_children_queryset().first()

    @cached_method
    def get_last_child(self):
        """Get the last child node or None if it has no children."""
        return self.get_children_queryset().last()

# The End
