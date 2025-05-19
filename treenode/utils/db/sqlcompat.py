# -*- coding: utf-8 -*-
"""
Database compatibility extension module.

Adapts SQL code to the specific features of SQL syntax of various
Database vendors.

Instead of direct concatenation:
old: p._path || '.' || LPAD(...)
new: SQLCompat.concat("p._path", "'.'", SQLCompat.lpad(...))

Instead of TO_HEX(...)
old: TO_HEX(...)
new: SQLCompat.to_hex(...)

Instead of LPAD(...)
old: LPAD(...)
new: SQLCompat.lpad(...)

Version: 3.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import connection
from .db_vendor import is_mysql, is_mariadb, is_sqlite, is_mssql
from ...settings import TREENODE_PAD_CHAR


class SQLCompat:
    """Vendor-Specific SQL Compatibility Layer."""

    @staticmethod
    def concat(*args):
        """Adapt string concatenation to the vendor-specific syntax."""
        args_joined = ", ".join(args)
        if is_mysql() or is_mariadb():
            return f"CONCAT({args_joined})"
        elif is_mssql():
            return " + ".join(args)
        else:
            return " || ".join(args)

    @staticmethod
    def to_hex(value):
        """Convert integer to uppercase hexadecimal string."""
        if is_sqlite():
            return f"UPPER(printf('%x', {value}))"
        elif is_mysql() or is_mariadb():
            return f"UPPER(CONV({value}, 10, 16))"
        else:
            return f"UPPER(TO_HEX({value}))"

    @staticmethod
    def lpad(value, length, char=TREENODE_PAD_CHAR):
        """Pad string to the specified length."""
        if is_sqlite():
            return f"printf('%0{length}s', {value})"
        else:
            return f"LPAD({value}, {length}, {char})"

    @staticmethod
    def update_from(db_table, cte_header, base_sql, recursive_sql, update_fields):
        """
        Generate final SQL for updating via recursive CTE.

        PostgreSQL uses UPDATE ... FROM.
        Other engines use vendor-specific strategies.
        """
        qt = connection.ops.quote_name(db_table)
        def qf(f): return connection.ops.quote_name(f)

        cte_alias = {
            "priority": "new_priority",
            "_path": "new_path",
            "_depth": "new_depth",
        }

        if connection.vendor == "postgresql":
            set_clause = ", ".join(
                f"{qf(f)} = t.{cte_alias.get(f, f)}" for f in update_fields
            )
            return f"""
                WITH RECURSIVE tree_cte {cte_header} AS (
                    {base_sql}
                    UNION ALL
                    {recursive_sql}
                )
                UPDATE {qt} AS orig
                SET {set_clause}
                FROM tree_cte t
                WHERE orig.id = t.id;
            """

        elif connection.vendor in {"microsoft", "mssql"}:
            set_clause = ", ".join(
                f"{qt}.{f} = t.{f}" for f in update_fields
            )
            return f"""
                WITH tree_cte {cte_header} AS (
                    {base_sql}
                    UNION ALL
                    {recursive_sql}
                )
                UPDATE orig
                SET {set_clause}
                FROM {qt} AS orig
                JOIN tree_cte t ON orig.id = t.id;
            """

        elif connection.vendor == "oracle":
            set_clause = ", ".join(
                f"orig.{f} = t.{f}" for f in update_fields
            )
            return f"""
                WITH tree_cte {cte_header} AS (
                    {base_sql}
                    UNION ALL
                    {recursive_sql}
                )
                MERGE INTO {qt} orig
                USING tree_cte t
                ON (orig.id = t.id)
                WHEN MATCHED THEN UPDATE SET
                    {set_clause};
            """

        elif connection.vendor == "sqlite":
            # SQLite workaround via temporary table
            temp_table = "temp_tree_update"
            cols = ["id"] + [cte_alias.get(f, f) for f in update_fields]
            col_defs = ", ".join(f"{c} TEXT" for c in cols)
            insert_cols = ", ".join(cols)
            select_cols = ", ".join(cols)

            set_clause = ", ".join(
                f"{qf(f)} = (SELECT t.{cte_alias.get(f, f)} FROM {temp_table} t WHERE t.id = {qt}.id)"  # noqa
                for f in update_fields
            )

            return f"""
                DROP TABLE IF EXISTS {temp_table};
                CREATE TEMP TABLE {temp_table} ({col_defs});

                WITH RECURSIVE tree_cte {cte_header} AS (
                    {base_sql}
                    UNION ALL
                    {recursive_sql}
                )
                INSERT INTO {temp_table} ({insert_cols})
                SELECT {select_cols} FROM tree_cte;

                UPDATE {qt}
                SET {set_clause}
                WHERE id IN (SELECT id FROM {temp_table});
            """

        else:
            # Fallback: subqueries
            # (still buggy in SQLite, hence above workaround)
            set_clause = ", ".join(
                f"{qf(f)} = (SELECT t.{f} FROM tree_cte t WHERE t.id = {qt}.id)"
                for f in update_fields
            )
            where_clause = "id IN (SELECT id FROM tree_cte)"
            return f"""
                WITH RECURSIVE tree_cte {cte_header} AS (
                    {base_sql}
                    UNION ALL
                    {recursive_sql}
                )
                UPDATE {qt}
                SET {set_clause}
                WHERE {where_clause};
            """

# The End
