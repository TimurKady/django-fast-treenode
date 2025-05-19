# -*- coding: utf-8 -*-
"""
Low-level SQL Query Manager.

Encapsulates all logic to retrieve related primary keys based on relationships
(e.g., ancestors, children, descendants, siblings, family, root) using raw SQL.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import connection
from ..utils.db.sqlcompat import SQLCompat 


class TreeQuery:
    """Class to manage tree-structure SQL queries."""

    def __init__(self, instance):
        """Initialize with the given model instance."""
        self.node = instance
        self.db_table = instance._meta.db_table

    def __call__(self, *args, **kwargs):
        """Call function."""
        return self.get_relative_pks(*args, **kwargs)

    def execute_query(self, sql, params):
        """Execute the given SQL with parameters and fetch all the results."""
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def order_by(self, sql, order_by_clause):
        """Wrap the SQL in an outer query to enforce ordering."""
        return f"SELECT * FROM ({sql}) AS combined ORDER BY {order_by_clause}"

    def get_children(self):
        """
        Build SQL for the 'children' relationship.

        The current node is not included.
        """
        sql = f"SELECT id, priority FROM {self.db_table} WHERE parent_id = %s ORDER BY priority"  # noqa: D501
        params = [self.node.pk]
        return sql, params

    def get_siblings(self, include_self=True):
        """
        Build SQL for the 'siblings' relationship.

        If include_self is True, the current node is included by performing
        a UNION ALL.
        """
        if self.node.parent_id is None:
            sql1 = f"SELECT id, priority FROM {self.db_table} WHERE parent_id IS NULL AND id <> %s"  # noqa: D501
            params1 = [self.node.pk]
        else:
            sql1 = f"SELECT id, priority FROM {self.db_table} WHERE parent_id = %s AND id <> %s"  # noqa: D501
            params1 = [self.node.parent_id, self.node.pk]

        if include_self:
            sql2 = f"SELECT id, priority FROM {self.db_table} WHERE id = %s"
            params2 = [self.node.pk]
            combined_sql, combined_params = SQLCompat.wrap_union_all(
                [(sql1, params1), (sql2, params2)])
            sql = self.order_by(combined_sql, "priority")
            return sql, combined_params
        else:
            sql = self.order_by(sql1, "priority")
            return sql, params1

    def get_descendants(self, include_self, depth):
        """
        Build SQL for the 'descendants'.

        Relationship using startswith-like logic.
        Avoids locale-dependent string comparison issues by relying on
        _path LIKE 'xxx.%'.
        """
        like_pattern = self.node._path + '.%'  # emulate startswith

        base_sql = f"""
            SELECT id, _depth, priority
            FROM {self.db_table}
            WHERE _path LIKE %s
        """
        params = [like_pattern]

        if depth is not None:
            depth_val = getattr(self.node, "_depth", None)
            if depth_val is None:
                depth_val = type(self.node).objects.values_list(
                    "_depth", flat=True).get(pk=self.node.pk)
            base_sql += " AND _depth <= %s"
            params.append(depth_val + depth)

        if include_self:
            sql_self = f"""
                SELECT id, _depth, priority
                FROM {self.db_table}
                WHERE id = %s
            """
            union_sql, union_params = SQLCompat.wrap_union_all([
                (base_sql, params),
                (sql_self, [self.node.pk])
            ])
        else:
            union_sql, union_params = base_sql, params

        union_sql = self.order_by(union_sql, "_depth, priority")
        return union_sql, union_params

    '''
    def get_descendants(self, include_self, depth):
        """
        Build SQL for the 'descendants' relationship.

        Optionally limits the depth, and includes the current node if requested.
        """
        from_path = self.node._path + "."
        to_path = self.node._path + "/"
        base_sql = f"SELECT id, _depth, priority FROM {self.db_table} WHERE _path >= %s AND _path < %s"  # noqa: D501
        params = [from_path, to_path]

        if depth is not None:
            # Use values_list to fetch _depth without loading the full model
            depth_val = getattr(self.node, "_depth", None)
            if depth_val is None:
                depth_val = type(self.node).objects.values_list(
                    "_depth", flat=True).get(pk=self.node.pk)
            base_sql += " AND _depth <= %s"
            params.append(depth_val + depth)

        if include_self:
            sql_self = f"SELECT id, _depth, priority FROM {self.db_table} WHERE id = %s"  # noqa: D501
            union_sql, union_params = SQLCompat.wrap_union_all(
                [(base_sql, params), (sql_self, [self.node.pk])])
        else:
            union_sql, union_params = base_sql, params

        union_sql = self.order_by(union_sql, "_depth, priority")
        return union_sql, union_params
    '''

    def get_ancestors(self, include_self):
        """
        Retrieve ancestors using a recursive CTE.

        Returns the list of IDs in order (from root to immediate parent).
        """
        sql = (
            f"WITH RECURSIVE ancestors_cte(id, lvl) AS ("
            f"  SELECT (SELECT parent_id FROM {self.db_table} WHERE id = %s), 1 "  # noqa: D501
            f"  UNION ALL "
            f"  SELECT p.parent_id, lvl + 1 FROM ancestors_cte a "
            f"  JOIN {self.db_table} p ON p.id = a.id "
            f"  WHERE a.id IS NOT NULL"
            f") "
            f"SELECT id FROM ancestors_cte WHERE id IS NOT NULL"
        )
        params = [self.node.pk]
        rows = self.execute_query(sql, params)
        ancestor_ids = [row[0] for row in rows]
        if include_self:
            ancestor_ids.insert(0, self.node.pk)
        # Reverse the order to get from the root to the immediate parent.
        return ancestor_ids[::-1]

    def get_family(self, include_self, depth):
        """
        Build SQL for the 'family' relationship.

        Family is defined as the union of ancestors and descendants.
        The ancestors condition uses _path less than current node’s _path,
        and the descendants condition uses a range on _path.
        """
        ancestors_condition = "_path < %s"
        descendants_condition = "(_path >= %s AND _path < %s)"
        family_sql = f"SELECT id, _depth, priority FROM {self.db_table} WHERE {ancestors_condition} OR {descendants_condition}"  # noqa: D501
        params = [self.node._path, self.node._path + ".", self.node._path + "/"]

        queries = [(family_sql, params)]
        if include_self:
            sql_self = f"SELECT id, _depth, priority FROM {self.db_table} WHERE id = %s"  # noqa: D501
            queries.append((sql_self, [self.node.pk]))
        combined_sql, combined_params = SQLCompat.wrap_union_all(queries)
        combined_sql = self.order_by(combined_sql, "_depth, priority")
        return combined_sql, combined_params

    def get_root(self):
        """
        Build SQL for the 'root' relationship.

        Retrieves the root node, identified by the first segment of _path.
        """
        segments = self.node._path.split(".")
        root_segment = segments[0]
        sql = f"SELECT id, priority FROM {self.db_table} WHERE _path = %s ORDER BY priority"  # noqa: D501
        params = [root_segment]
        return sql, params

    def get_relative_pks(self, objects="children", include_self=True, depth=None, mode=None):  # noqa: D501
        """
        Get related primary keys from the tree using raw SQL queries.

        Arguments:
            objects (str): Relationship type. Options are: "ancestors",
                           "children", "descendants", "family", "root", or
                           "siblings".
            include_self (bool): Whether to include the current node in the
                           result (ignored for 'children').
            depth (int|None): Maximum depth to consider (only for 'descendants'
                           and 'family').
            mode (str|None): 'count' returns the number of nodes, 'exist'
                           returns a boolean, or None returns a list of IDs.

        Returns:
            list | int | bool: Depending on mode, returns a list of IDs, count,
                           or boolean.
        """
        if objects == "children":
            sql, params = self.get_children()
        elif objects == "siblings":
            sql, params = self.get_siblings(include_self=include_self)
        elif objects == "descendants":
            sql, params = self.get_descendants(include_self, depth)
        elif objects == "ancestors":
            result = self.get_ancestors(include_self)
            if mode == "count":
                return len(result)
            elif mode == "exist":
                return bool(result)
            else:
                return result
        elif objects == "family":
            sql, params = self.get_family(include_self, depth)
        elif objects == "root":
            sql, params = self.get_root()
        else:
            raise ValueError(f"Unknown relationship type: {objects}")

        # Execute the query for all branches except 'ancestors'
        rows = self.execute_query(sql, params)
        result_ids = [row[0] for row in rows]

        if mode == "count":
            return len(result_ids)
        elif mode == "exist":
            return bool(result_ids)
        else:
            return result_ids


class TreeQueryManager:
    """Desctiptor for TreeQueryManager."""

    def __get__(self, instance, owner):
        """Get query for instance."""
        if instance is None:
            return self
        return TreeQuery(instance)
