# -*- coding: utf-8 -*-
"""
Adjacency List Manager and QuerySet

This module defines custom managers and query sets for the Adjacency List.
It includes operations for synchronizing with the model implementing
the Closure Table.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from collections import deque, defaultdict
from django.db import models, transaction
from django.db import connection


class TreeNodeQuerySet(models.QuerySet):
    """TreeNodeModel QuerySet."""

    def __init__(self, model=None, query=None, using=None, hints=None):
        # First we call the parent class constructor
        super().__init__(model, query, using, hints)

    def create(self, **kwargs):
        """Ensure that the save logic is executed when using create."""
        obj = self.model(**kwargs)
        obj.save()
        return obj

    def update(self, **kwargs):
        """Update node with synchronization of tn_parent change."""
        tn_parent_changed = 'tn_parent' in kwargs
        # Save pks of updated objects
        pks = list(self.values_list('pk', flat=True))
        # Clone the query and clear the ordering to avoid an aggregation error
        qs = self._clone()
        qs.query.clear_ordering()
        result = super(TreeNodeQuerySet, qs).update(**kwargs)
        if tn_parent_changed and pks:
            objs = list(self.model.objects.filter(pk__in=pks))
            self.model.closure_model.objects.bulk_update(objs, ['tn_parent'])
        return result

    def get_or_create(self, defaults=None, **kwargs):
        """Ensure that the save logic is executed when using get_or_create."""
        defaults = defaults or {}
        created = False
        obj = self.filter(**kwargs).first()
        if obj is None:
            params = {k: v for k, v in kwargs.items() if "__" not in k}
            params.update(
                {k: v() if callable(v) else v for k, v in defaults.items()}
            )
            obj = self.create(**params)
            created = True
        return obj, created

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        """Update or create."""
        defaults = defaults or {}
        create_defaults = create_defaults or {}

        with transaction.atomic():
            obj = self.filter(**kwargs).first()
            params = {k: v for k, v in kwargs.items() if "__" not in k}
            if obj is None:
                params.update({k: v() if callable(v) else v for k,
                              v in create_defaults.items()})
                obj = self.create(**params)
                created = True
            else:
                params.update(
                    {k: v() if callable(v) else v for k, v in defaults.items()})
                for field, value in params.items():
                    setattr(obj, field, value)
                obj.save(update_fields=params.keys())
                created = False
        return obj, created

    def bulk_create(self, objs, batch_size=1000, *args, **kwargs):
        """
        Bulk create.

        Method of bulk creation objects with updating and processing of
        the Closuse Model.
        """
        # 1. Bulk Insertion of Nodes in Adjacency Models
        objs = super().bulk_create(objs, batch_size, *args, **kwargs)
        # 2. Synchronization of the Closing Model
        self.model.closure_model.objects.bulk_create(objs)
        # 3. Clear cache and return result
        self.model.clear_cache()
        return objs

    def bulk_update(self, objs, fields, batch_size=1000):
        """Bulk update with synchronization of tn_parent change."""
        # Clone the query and clear the ordering to avoid an aggregation error
        qs = self._clone()
        qs.query.clear_ordering()
        # Perform an Adjacency Model Update
        result = super(TreeNodeQuerySet, qs).bulk_update(
            objs, fields, batch_size
        )
        # Synchronize data in the Closing Model
        if 'tn_parent' in fields:
            self.model.closure_model.objects.bulk_update(
                objs, ['tn_parent'], batch_size
            )
        return result


class TreeNodeModelManager(models.Manager):
    """TreeNodeModel Manager."""

    def bulk_create(self, objs, batch_size=1000, ignore_conflicts=False):
        """
        Bulk Create.

        Override bulk_create for the adjacency model.
        Here we first clear the cache, then delegate the creation via our
        custom QuerySet.
        """
        self.model.clear_cache()
        result = self.get_queryset().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )
        transaction.on_commit(lambda: self._update_auto_increment())
        return result

    def bulk_update(self, objs, fields=None, batch_size=1000):
        """Bulk Update."""
        self.model.clear_cache()
        result = self.get_queryset().bulk_update(objs, fields, batch_size)
        return result

    def get_queryset(self):
        """Return a sorted QuerySet."""
        queryset = TreeNodeQuerySet(self.model, using=self._db)\
            .annotate(_depth_db=models.Max("parents_set__depth"))\
            .order_by("_depth_db", "tn_parent", "tn_priority")
        return queryset

    # Service methods -------------------

    def _bulk_update_tn_closure(self, objs, fields=None, batch_size=1000):
        """Update tn_closure in bulk."""
        self.model.clear_cache()
        super().bulk_update(objs, fields, batch_size)

    def _get_auto_increment_sequence(self):
        """Get auto increment sequence."""
        table_name = self.model._meta.db_table
        pk_column = self.model._meta.pk.column
        with connection.cursor() as cursor:
            query = "SELECT pg_get_serial_sequence(%s, %s)"
            cursor.execute(query, [table_name, pk_column])
            result = cursor.fetchone()
        return result[0] if result else None

    def _update_auto_increment(self):
        """Update auto increment."""
        table_name = self.model._meta.db_table
        with connection.cursor() as cursor:
            db_engine = connection.vendor

            if db_engine == "postgresql":
                sequence_name = self._get_auto_increment_sequence()
                # Get the max id from the table
                cursor.execute(
                    f"SELECT COALESCE(MAX(id), 0) FROM {table_name};"
                )
                max_id = cursor.fetchone()[0]
                next_id = max_id + 1
                # Directly specify the next value of the sequence
                cursor.execute(
                    f"ALTER SEQUENCE {sequence_name} RESTART WITH {next_id};"
                )
            elif db_engine == "mysql":
                cursor.execute(f"SELECT MAX(id) FROM {table_name};")
                max_id = cursor.fetchone()[0] or 0
                next_id = max_id + 1
                cursor.execute(
                    f"ALTER TABLE {table_name} AUTO_INCREMENT = {next_id};"
                )
            elif db_engine == "sqlite":
                cursor.execute(
                    f"UPDATE sqlite_sequence SET seq = (SELECT MAX(id) \
FROM {table_name}) WHERE name='{table_name}';"
                )
            elif db_engine == "mssql":
                cursor.execute(f"SELECT MAX(id) FROM {table_name};")
                max_id = cursor.fetchone()[0] or 0
                cursor.execute(
                    f"DBCC CHECKIDENT ('{table_name}', RESEED, {max_id});"
                )
            else:
                raise NotImplementedError(
                    f"Autoincrement for {db_engine} is not supported."
                )

# The End
