# -*- coding: utf-8 -*-
"""
Tree update task compiler class.

Compiles tasks to low-level SQL to update the materialized path (_path), depth
(_depth), and node order (priority) when they are shifted or moved.

Version: 3.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import connection

from ...settings import SEGMENT_LENGTH
from .sqlcompat import SQLCompat


class TreePathCompiler:
    """
    Tree Task compiler class.

    Efficient, ORM-free computation of _path, _depth and priority
    for tree structures based on Materialized Path.
    """

    @classmethod
    def update_path(cls, model, parent_id=None):
        """Rebuild subtree using BFS so parents update before children."""
        table = model._meta.db_table
        sort_field = model.sorting_field

        def fetch_children(pid):
            if pid is None:
                where = "parent_id IS NULL"
                params = []
            else:
                where = "parent_id = %s"
                params = [pid]
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT id FROM {table} WHERE {where} ORDER BY {sort_field}, id",
                    params,
                )
                return [row[0] for row in cursor.fetchall()]

        queue = []

        if parent_id is None:
            for idx, node_id in enumerate(fetch_children(None)):
                queue.append((node_id, "", 0, idx))
        else:
            parent_data = model.objects.filter(pk=parent_id).values("_path", "_depth").first()
            parent_path = parent_data["_path"] if parent_data else ""
            depth = (parent_data["_depth"] + 1) if parent_data else 0
            for idx, node_id in enumerate(fetch_children(parent_id)):
                queue.append((node_id, parent_path, depth, idx))

        while queue:
            node_id, base_path, depth, index = queue.pop(0)
            segment = f"{index:0{SEGMENT_LENGTH}X}"
            path = segment if base_path == "" else f"{base_path}.{segment}"
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table} SET priority=%s, _path=%s, _depth=%s WHERE id=%s",
                    [index, path, depth, node_id],
                )
            for child_idx, child_id in enumerate(fetch_children(node_id)):
                queue.append((child_id, path, depth + 1, child_idx))


# The End
