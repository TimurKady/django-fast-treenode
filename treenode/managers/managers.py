# -*- coding: utf-8 -*-
"""
Manager and Query Set Customization Module

This module defines custom managers and query sets for the TreeNodeModel.
It includes operations for synchronizing additional fields associated with
the Materialized Path method implementation.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models  # , transaction
from django.utils.translation import gettext_lazy as _
import logging

from ..cache import treenode_cache as cache


class TreeNodeQuerySet(models.QuerySet):
    """TreeNodeModel QuerySet."""

    def create(self, **kwargs):
        """Create an object."""
        obj = self.model(**kwargs)
        obj.save()
        return obj

    def get_or_create(self, defaults=None, **kwargs):
        """Get or create an object."""
        defaults = defaults or {}
        created = False

        try:
            obj = super().get(**kwargs)
        except models.DoesNotExist:
            params = {k: v for k, v in kwargs.items() if "__" not in k}
            params.update(
                {k: v() if callable(v) else v for k, v in defaults.items()}
            )
            obj = self.model(**params)
            obj.save()
            created = True
        return obj, created

    def update(self, **kwargs):
        """Update method for TreeNodeQuerySet.

        If kwargs contains updates for 'parent' or 'priority',
        then specialized bulk_update logic is used, which:
        - Updates allowed fields directly;
        - If parent is updated, calls _bulk_move (updates _path and parent);
        - If priority is updated (without parent), updates sibling order.
        Otherwise, the standard update is called.
        """
        forbidden = {'_path', '_depth'}
        if forbidden.intersection(kwargs.keys()):
            raise ValueError(
                _(f"Fields cannot be updated directly: {', '.join(forbidden)}")
            )

        result = 0
        excluded_fields = {"parent", "priority", "_path", "_depth"}
        params = {key: value for key,
                  value in kwargs.items() if key not in excluded_fields}

        if params:
            # Normal update
            result = super().update(**params)

        cache.invalidate(self.model._meta.label)
        return result

    def update_or_create(self, defaults=None, **kwargs):
        """Update or create an object."""
        params = {**(defaults or {}), **kwargs}
        created = False
        try:
            obj = super().get(**kwargs)
            obj.update(**params)
        except models.DoesNotExist:
            obj = self.model(**params)
            obj.save()
            created = True
        return obj, created

    def _raw_update(self, **kwargs):
        """
        Bypass custom update() logic (e.g. field protection).

        WARNING: Unsafe low-level update bypassing all TreeNode protections.
        Use only when bypassing _path/_depth/priority safety checks is
        intentional.
        """
        result = models.QuerySet(self.model, using=self.db).update(**kwargs)
        return result

    #  batch_size=None, **kwargs):
    def _raw_bulk_update(self, objs, fields, *args, **kwargs):
        """
        Bypass custom bulk_update logic (e.g. field protection).

        WARNING: Unsafe low-level update bypassing all TreeNode protections.
        Use only when bypassing _path/_depth/priority safety checks is
        intentional.
        """
        base_qs = models.QuerySet(self.model, using=self.db)
        result = base_qs.bulk_update(objs, fields, *args, **kwargs)

        return result

    def _raw_delete(self, using=None):
        return models.QuerySet(self.model, using=using or self.db)\
            ._raw_delete(using=using or self.db)

    def __iter__(self):
        """Iterate queryset."""
        try:
            if len(self.model.tasks.queue) > 0:
                # print("🌲 TreeNodeQuerySet: auto-run (iter)")
                self.model.tasks.run()
        except Exception as e:
            logging.error("⚠️ Tree flush failed silently (iter): %s", e)
        return super().__iter__()

    def _fetch_all(self):
        """Extract data for a queryset from the database."""
        try:
            tasks = self.model.tasks
            if len(tasks.queue) > 0:
                # print("🌲 TreeNodeQuerySet: auto-run (_fetch_all)")
                tasks.run()
        except Exception as e:
            logging.error("⚠️ Tree flush failed silently: %s", e)
        super()._fetch_all()

# ------------------------------------------------------------------
#
# Managers
#
# ------------------------------------------------------------------


class TreeNodeManager(models.Manager):
    """Tree Manager Class."""

    def get_queryset(self):
        """Get QuerySet."""
        return TreeNodeQuerySet(self.model, using=self._db).order_by(
            "_depth", "priority"
        )

    def bulk_create(self, objs, *args, **kwargs):
        """Create objects in bulk and schedule tree rebuilds."""
        result = super().bulk_create(objs, *args, **kwargs)

        # Collect parent_ids, stop at first None
        parent_ids = set()
        for obj in objs:
            pid = obj.parent_id
            if pid is None:
                self.model.tasks.queue.clear()
                self.model.tasks.add("update", None)
                break
            parent_ids.add(pid)
        else:
            for pid in parent_ids:
                self.model.tasks.add("update", pid)

        # self.model.tasks.run()
        return result

    def bulk_update(self, objs, fields, batch_size=None):
        """Update objects in bulk and schedule tree rebuilds if needed."""
        result = super().bulk_update(objs, fields, batch_size)

        parent_ids = set()
        for obj in objs:
            pid = obj.parent_id
            if pid is None:
                self.model.tasks.queue.clear()
                self.model.tasks.add("update", None)
                break
            parent_ids.add(pid)
        else:
            for pid in parent_ids:
                self.model.tasks.add("update", pid)

        # self.model.tasks.run()
        return result

    def _raw_update(self, *args, **kwargs):
        """
        Update objects in bulk.

        WARNING: Unsafe low-level update bypassing all TreeNode protections.
        Use only when bypassing _path/_depth/priority safety checks is
        intentional.
        """
        return models.QuerySet(self.model, using=self.db)\
            .update(*args, **kwargs)

    def _raw_bulk_update(self, *args, **kwargs):
        """
        Update objects in bulk.

        WARNING: Unsafe low-level update bypassing all TreeNode protections.
        Use only when bypassing _path/_depth/priority safety checks is
        intentional.
        """
        return models.QuerySet(self.model, using=self.db)\
            .bulk_update(*args, **kwargs)


# The End
