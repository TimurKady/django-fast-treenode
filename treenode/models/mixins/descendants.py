# -*- coding: utf-8 -*-
"""
TreeNode Descendants Mixin

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


class TreeNodeDescendantsMixin(models.Model):
    """TreeNode Descendants Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def get_descendants_queryset(self, include_self=False, depth=None):
        """Get the descendants queryset."""
        path = self.get_order()  # calls refresh and gets the current _path

        # from_path = path + '.'
        # to_path = path + '/'

        # options = {'_path__gte': from_path, '_path__lt': to_path}
        # if depth:
        #    options["_depth__lt"] = depth
        # queryset = self._meta.model.objects.filter(**options)
        # if include_self:
        #     return self._meta.model.objects.filter(pk=self.pk) | queryset
        # else:
        #    return queryset

        suffix = "" if include_self else '.'
        path += suffix
        cls = self._meta.model
        queryset = cls.objects.filter(_path__startswith=path)
        ordering_fields = [
            "priority",
            "id",
        ] if cls.sorting_field == "priority" else [cls.sorting_field]
        prefix = "" if cls.sorting_direction == cls.SortingChoices.ASC else "-"
        order_args = [prefix + ordering_fields[0]] + ordering_fields[1:]
        return queryset.order_by(*order_args)

    @cached_method
    def get_descendants_pks(self, include_self=False, depth=None):
        """Get the descendants pks list."""
        return self.query("descendants", include_self)

    # @profile
    @cached_method
    def get_descendants(self, include_self=False, depth=None):
        """Get a list containing all descendants."""
        # descendants_pks = self.query("descendants", include_self)
        # queryset = self._meta.model.objects.filter(pk__in=descendants_pks)
        queryset = self.get_descendants_queryset(include_self, depth)
        return list(queryset)

    @cached_method
    def get_descendants_count(self, include_self=False, depth=None):
        """Get the descendants count."""
        return self.query(
            objects="descendants",
            include_self=include_self,
            mode='count'
        )


# The End
