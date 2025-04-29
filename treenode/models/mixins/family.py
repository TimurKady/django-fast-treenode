# -*- coding: utf-8 -*-
"""
TreeNode Descendants Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models
from django.db.models import Q
from ...cache import cached_method


'''
try:
    profile
except NameError:
    def profile(func):
        """Profile."""
        return func
'''


class TreeNodeFamilyMixin(models.Model):
    """TreeNode Family Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def get_family_queryset(self):
        """
        Return node family.

        Return a QuerySet containing the ancestors, itself and the descendants,
        in tree order.
        """
        return self._meta.model.objects.filter(
            Q(pk__in=self._get_path()) |
            Q(_path__startswith=self._path+'.')
        )

    @cached_method
    def get_family_pks(self):
        """
        Return node family.

        Return a pk-list containing the ancestors, the model itself and
        the descendants, in tree order.
        """
        return self.query(objects="family")

    # @profile
    @cached_method
    def get_family(self):
        """
        Return node family.

        Return a list containing the ancestors, the model itself and
        the descendants, in tree order.
        """
        ancestors = self.get_ancestors()
        descendants = self.get_descendants()
        return ancestors.extend(descendants)

    @cached_method
    def get_family_count(self):
        """Return number of nodes in family."""
        return self.query(objects="family", mode='count')

# The End
