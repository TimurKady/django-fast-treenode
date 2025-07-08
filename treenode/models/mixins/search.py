# -*- coding: utf-8 -*-
"""
TreeNode Search Mixin

Version: 3.2.1
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models


class TreeNodeSearchMixin(models.Model):
    """Mixin that provides helper methods for quick node lookup."""

    class Meta:
        """Mixin Meta Class."""
        abstract = True

    @classmethod
    def find_by_path(cls, path, attr="id", delimiter="/"):
        """Return a node referenced by breadcrumbs path.

        The ``path`` argument may be a string or an iterable of breadcrumb
        values previously produced by :py:meth:`get_breadcrumbs`.
        If the path cannot be resolved, ``None`` is returned.
        """
        if path is None:
            return None

        if not isinstance(path, (list, tuple)):
            path = [p for p in str(path).strip(delimiter).split(delimiter) if p]

        parent = None
        for token in path:
            lookup = {attr: token}
            if parent is None:
                qs = cls.objects.filter(parent_id__isnull=True, **lookup)
            else:
                qs = cls.objects.filter(parent=parent, **lookup)
            parent = qs.first()
            if parent is None:
                return None
        return parent

    @classmethod
    def find_in_subtree(cls, parent, value, attr="id"):
        """Search ``parent`` descendants for attribute ``attr`` equal to ``value``."""
        if parent is None:
            return None
        prefix = parent.get_order() + "."
        return cls.objects.filter(_path__startswith=prefix, **{attr: value}).first()


# The End
