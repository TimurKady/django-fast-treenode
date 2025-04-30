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
        """
        Rebuild subtree starting from parent_id.

        If parent_id=None, then the whole tree is rebuilt.
        Uses only fields: parent_id and id. All others (priority, _path,
        _depth) are recalculated.
        """
        db_table = model._meta.db_table
        # Will eliminate the risk if the user names the model order or user.
        qname = connection.ops.quote_name(db_table)

        sorting_field = model.sorting_field
        sorting_fields = ["priority", "id"] if sorting_field == "priority" else [sorting_field]  # noqa: D5017
        sort_expr = ", ".join([
            f"c.{field}" if "." not in field else field
            for field in sorting_fields
        ])

        cte_header = "(id, parent_id, new_priority, new_path, new_depth)"

        row_number_expr = f"ROW_NUMBER() OVER (ORDER BY {sort_expr}) - 1"
        hex_expr = SQLCompat.to_hex(row_number_expr)
        lpad_expr = SQLCompat.lpad(hex_expr, SEGMENT_LENGTH, "'0'")

        if parent_id is None:
            new_path_expr = lpad_expr
            base_sql = f"""
                SELECT
                    c.id,
                    c.parent_id,
                    {row_number_expr} AS new_priority,
                    {new_path_expr} AS new_path,
                    0 AS new_depth
                FROM {qname} AS c
                WHERE c.parent_id IS NULL
            """
            params = []
        else:
            path_expr = SQLCompat.concat("p._path", "'.'", lpad_expr)
            base_sql = f"""
                SELECT
                    c.id,
                    c.parent_id,
                    {row_number_expr} AS new_priority,
                    {path_expr} AS new_path,
                    p._depth + 1 AS new_depth
                FROM {qname} c
                JOIN {qname} p ON c.parent_id = p.id
                WHERE p.id = %s
            """
            params = [parent_id]

        recursive_row_number_expr = f"ROW_NUMBER() OVER (PARTITION BY c.parent_id ORDER BY {sort_expr}) - 1"
        recursive_hex_expr = SQLCompat.to_hex(recursive_row_number_expr)
        recursive_lpad_expr = SQLCompat.lpad(
            recursive_hex_expr, SEGMENT_LENGTH, "'0'")
        recursive_path_expr = SQLCompat.concat(
            "t.new_path", "'.'", recursive_lpad_expr)

        recursive_sql = f"""
            SELECT
                c.id,
                c.parent_id,
                {recursive_row_number_expr} AS new_priority,
                {recursive_path_expr} AS new_path,
                t.new_depth + 1 AS new_depth
            FROM {qname} c
            JOIN tree_cte t ON c.parent_id = t.id
        """

        final_sql = SQLCompat.update_from(
            db_table=db_table,
            cte_header=cte_header,
            base_sql=base_sql,
            recursive_sql=recursive_sql,
            update_fields=["priority", "_path", "_depth"]
        )

        with connection.cursor() as cursor:
            # Make params read-only
            params = tuple(params)
            cursor.execute(final_sql, params)


# The End
