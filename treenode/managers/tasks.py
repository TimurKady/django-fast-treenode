# -*- coding: utf-8 -*-
"""
TreeNode TaskQuery manager

Version: 3.0.4
Author: Timur Kady
Email: timurkady@yandex.com
"""

import atexit
from django.db import connection, transaction

from ..utils.db import TreePathCompiler


class TreeTaskQueue:
    """TreeTaskQueue Class."""

    def __init__(self, model):
        """Init the task query."""
        self.model = model
        self.queue = []
        self._running = False

        # Register the execution queue when the interpreter exits
        atexit.register(self._atexit_run)

    def _atexit_run(self):
        """Run queue on interpreter exit if pending tasks exist."""
        if self.queue and not self._running:
            try:
                self.run()
            except Exception as e:
                # Don't crash on completion, just log
                print(f"[TreeTaskQueue] Error during atexit: {e}")

    def add(self, mode, parent_id):
        """Add task to the queue.

        Parameters:
            mode (str): Task type (currently only "update").
            parent_id (int|None): ID of parent node to update from (None = full tree).
        """
        self.queue.append({"mode": mode, "parent_id": parent_id})

    def run(self):
        """Run task queue.

        This method collects all queued tasks, optimizes them, and performs
        a recursive rebuild of tree paths and depths using SQL. Locks the
        required rows before running.

        Uses Django's `transaction.atomic()` to ensure that any recursive CTE
        execution or SAVEPOINT creation works properly under PostgreSQL.
        """
        if len(self.queue) == 0:
            return

        self._running = True
        try:
            optimized = self._optimize()
            if not optimized:
                return

            parent_ids = [t["parent_id"] for t in optimized if t["parent_id"] is not None]

            with transaction.atomic():
                if any(t["parent_id"] is None for t in optimized):
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                f"SELECT id FROM {self.model._meta.db_table} WHERE parent_id IS NULL FOR UPDATE NOWAIT"
                            )
                    except Exception as e:
                        print(f"[TreeTaskQueue] Skipped (root locked): {e}")
                        return
                else:
                    try:
                        with connection.cursor() as cursor:
                            for parent_id in parent_ids:
                                cursor.execute(
                                    f"SELECT id FROM {self.model._meta.db_table} WHERE id = %s FOR UPDATE NOWAIT",
                                    [parent_id],
                                )
                    except Exception as e:
                        print(f"[TreeTaskQueue] Skipped (parent locked): {e}")
                        return

                for task in optimized:
                    if task["mode"] == "update":
                        TreePathCompiler.update_path(
                            model=self.model,
                            parent_id=task["parent_id"]
                        )

        except Exception as e:
            print(f"[TreeTaskQueue] Error in run: {e}")
            connection.rollback()
        finally:
            self.queue.clear()
            self._running = False

    def _optimize(self):
        """Return optimized task queue (ID-only logic).

        Attempts to merge redundant or overlapping subtree updates into
        the minimal set of unique parent IDs that need to be rebuilt.
        If it finds a common root, it returns a single task for full rebuild.
        """
        result_set = set()
        id_set = set()

        for task in self.queue:
            if task["mode"] == "update":
                parent_id = task["parent_id"]
                if parent_id is None:
                    return [{"mode": "update", "parent_id": None}]
                else:
                    id_set.add(parent_id)

        id_list = list(id_set)

        while id_list:
            current = id_list.pop(0)
            merged = False
            for other in id_list[:]:
                ancestor = self._get_common_ancestor(current, other)
                if ancestor is not None:
                    if ancestor in self._get_root_ids():
                        return [{"mode": "update", "parent_id": None}]
                    if ancestor not in id_set:
                        id_list.append(ancestor)
                        id_set.add(ancestor)
                    id_list.remove(other)
                    merged = True
                    break
            if not merged:
                result_set.add(current)

        return [{"mode": "update", "parent_id": pk} for pk in sorted(result_set)]

    def _get_root_ids(self):
        """Return root node IDs."""
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM {self.model._meta.db_table} WHERE parent_id IS NULL")
            return [row[0] for row in cursor.fetchall()]

    def _get_parent_id(self, node_id):
        """Return parent ID for a given node."""
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT parent_id FROM {self.model._meta.db_table} WHERE id = %s", [node_id])
            row = cursor.fetchone()
            return row[0] if row else None

    def _get_ancestor_path(self, node_id):
        """Return list of ancestor IDs including the node itself, using recursive SQL."""
        table = self.model._meta.db_table

        sql = f"""
            WITH RECURSIVE ancestor_cte AS (
                SELECT id, parent_id, 0 AS depth
                FROM {table}
                WHERE id = %s

                UNION ALL

                SELECT t.id, t.parent_id, a.depth + 1
                FROM {table} t
                JOIN ancestor_cte a ON t.id = a.parent_id
            )
            SELECT id FROM ancestor_cte ORDER BY depth DESC
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [node_id])
            rows = cursor.fetchall()

        return [row[0] for row in rows]

    def _get_common_ancestor(self, id1, id2):
        """Return common ancestor ID between two nodes."""
        path1 = self._get_ancestor_path(id1)
        path2 = self._get_ancestor_path(id2)
        common = None
        for a, b in zip(path1, path2):
            if a == b:
                common = a
            else:
                break
        return common


class TreeTaskManager:
    """Handle to TreeTaskQueue."""

    def __get__(self, instance, owner):
        """Get query for instance."""
        if not hasattr(owner, "_task_queue"):
            owner._task_queue = TreeTaskQueue(owner)
        return owner._task_queue


# The End
