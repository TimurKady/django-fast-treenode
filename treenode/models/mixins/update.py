# -*- coding: utf-8 -*-
"""
TreeNode Raw SQL Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import models, connection

from ...settings import SEGMENT_LENGTH, BASE
from ...utils.db.sqlcompat import SQLCompat


class RawSQLMixin(models.Model):
    """Raw SQL Mixin."""

    class Meta:
        """Meta Class."""

        abstract = True

    def refresh(self):
        """Refresh key fields from DB."""
        task_query = self._meta.model.tasks
        if len(task_query.queue) > 0:
            task_query.run()

        table = self._meta.db_table
        sql = f"SELECT priority, _path, _depth FROM {table} WHERE id = %s"
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.pk])
            row = cursor.fetchone()
            self.priority, self._path, self._depth = row

        self._parent_id = self.parent_pk
        self._priority = self.priority

    def _shift_siblings_forward(self):
        """
        Shift the priority of all siblings starting from self.priority.

        Uses direct SQL for maximum speed.
        """
        if (self.priority is None) or (self.priority >= BASE - 1):
            return

        db_table = self._meta.db_table

        if self.parent_id is None:
            where_clause = "parent_id IS NULL"
            params = [self.priority]
        else:
            where_clause = "parent_id = %s"
            params = [self.parent_id, self.priority]

        sql = f"""
            UPDATE {db_table}
            SET priority = priority + 1
            WHERE {where_clause} AND priority >= %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, params)

    def _update_path(self, parent_id):
        """
        Rebuild subtree starting from parent_id.

        If parent_id=None, then the whole tree is rebuilt.
        Only fields are used: parent_id and id. All others (priority, _path,
        _depth) are recalculated.
        """
        db_table = self._meta.db_table

        sorting_field = self.sorting_field
        sorting_fields = ["priority", "id"] if sorting_field == "priority" else [sorting_field]   # noqa: D501
        sort_expr = ", ".join([
            field if "." in field else f"c.{field}"
            for field in sorting_fields
        ])

        cte_header = "(id, parent_id, new_priority, new_path, new_depth)"

        row_number_expr = "ROW_NUMBER() OVER (ORDER BY {sort_expr}) - 1"
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
                FROM {db_table} AS c
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
                FROM {db_table} c
                JOIN {db_table} p ON c.parent_id = p.id
                WHERE p.id = %s
            """
            params = [parent_id]

        recursive_row_number_expr = "ROW_NUMBER() OVER (PARTITION BY c.parent_id ORDER BY {sort_expr}) - 1"   # noqa: D501
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
            FROM {db_table} c
            JOIN tree_cte t ON c.parent_id = t.id
        """

        final_sql = f"""
            WITH RECURSIVE tree_cte {cte_header} AS (
                {base_sql}
                UNION ALL
                {recursive_sql}
            )
            UPDATE {db_table} AS orig
            SET
                priority = t.new_priority,
                _path = t.new_path,
                _depth = t.new_depth
            FROM tree_cte t
            WHERE orig.id = t.id;
        """

        self.sqlq.append((final_sql.format(sort_expr=sort_expr), params))


# The End
