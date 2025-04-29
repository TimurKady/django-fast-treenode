# -*- coding: utf-8 -*-
"""
DB Vendor Utility Module

The module contains utilities related to optimizing the application's operation
with various types of Databases.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from __future__ import annotations
from django.db import models, connection


class SQLService:
    """SQL utility class bound to a specific model."""

    def __init__(self, model):
        """Init."""
        self.db_vendor = connection.vendor
        self.model = model
        self.table = model._meta.db_table

    def get_next_id(self):
        """Reliably get the next ID for this model on different DBMS."""
        if self.db_vendor == 'postgresql':
            seq_name = f"{self.table}_id_seq"
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT nextval('{seq_name}')")
                return cursor.fetchone()[0]

        elif self.db_vendor == 'oracle':
            seq_name = f"{self.table}_SEQ"
            with connection.cursor() as cursor:
                try:
                    cursor.execute(f"SELECT {seq_name}.NEXTVAL FROM DUAL")
                    return cursor.fetchone()[0]
                except Exception:
                    cursor.execute(
                        f"CREATE SEQUENCE {seq_name} START WITH 1 INCREMENT BY 1"
                    )
                    cursor.execute(f"SELECT {seq_name}.NEXTVAL FROM DUAL")
                    return cursor.fetchone()[0]

        elif self.db_vendor in ('sqlite', 'mysql'):
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT MAX(id) FROM {self.table}")
                row = cursor.fetchone()
                return (row[0] or 0) + 1

        else:
            raise NotImplementedError(
                f"get_next_id() not supported for DB vendor '{self.db_vendor}'")

    def reassign_children(self, old_parent_id, new_parent_id):
        """Set new parent to children."""
        sql = f"""
            UPDATE {self.table}
            SET parent_id = %s
            WHERE parent_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [new_parent_id, old_parent_id])


class ModelSQLService:
    """
    Decorate SQLService.

    Descriptor to bind SQLService to Django models via
    `db = ModelSQLService()`.
    """

    def __set_name__(self, owner, name):
        """Set name."""
        self.model = owner

    def __get__(self, instance, owner):
        """Get SQLService."""
        return SQLService(owner)

# The End
