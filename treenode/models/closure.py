from django.db import models, connection, transaction


class ClosureModel(models.Model):
    """
    Closure Table Model — переработанная версия с использованием SQL,
    без использования ORM для вставки, перемещения и удаления.
    Поддерживает полную rebuild-операцию и выборки предков/потомков.
    """
    parent_id = models.IntegerField()
    child_id = models.IntegerField()
    depth = models.PositiveIntegerField()

    class Meta:
        db_table = "yourapp_closuremodel"  # Заменить на имя closure-таблицы
        unique_together = ("parent_id", "child_id")
        indexes = [
            models.Index(fields=["parent_id", "child_id"]),
            models.Index(fields=["parent_id", "depth"]),
            models.Index(fields=["child_id", "depth"]),
            models.Index(fields=["parent_id", "child_id", "depth"]),
        ]

    def __str__(self):
        return f"{self.parent_id} → {self.child_id} ({self.depth})"

    @classmethod
    @transaction.atomic
    def insert_node(cls, node_id, parent_id):
        with connection.cursor() as cursor:
            if parent_id is None:
                cursor.execute(f"""
                    INSERT INTO {cls._meta.db_table} (parent_id, child_id, depth)
                    VALUES (%s, %s, 0)
                """, [node_id, node_id])
            else:
                cursor.execute(f"""
                    INSERT INTO {cls._meta.db_table} (parent_id, child_id, depth)
                    SELECT parent_id, %s, depth + 1
                    FROM {cls._meta.db_table}
                    WHERE child_id = %s
                    UNION ALL
                    SELECT %s, %s, 0
                """, [node_id, parent_id, node_id, node_id])

    @classmethod
    @transaction.atomic
    def move_node(cls, node_id, new_parent_id):
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {cls._meta.db_table} (parent_id, child_id, depth)
                SELECT supertree.parent_id, subtree.child_id, supertree.depth + subtree.depth + 1
                FROM {cls._meta.db_table} AS supertree
                JOIN {cls._meta.db_table} AS subtree ON subtree.parent_id = %s
                WHERE supertree.child_id = %s
            """, [node_id, new_parent_id])

            cursor.execute(f"""
                DELETE FROM {cls._meta.db_table}
                WHERE (parent_id, child_id) IN (
                    SELECT old.parent_id, old.child_id
                    FROM {cls._meta.db_table} AS old
                    LEFT JOIN (
                        SELECT supertree.parent_id, subtree.child_id
                        FROM {cls._meta.db_table} AS supertree
                        JOIN {cls._meta.db_table} AS subtree ON subtree.parent_id = %s
                        WHERE supertree.child_id = %s
                    ) AS new_rel
                    ON old.parent_id = new_rel.parent_id AND old.child_id = new_rel.child_id
                    WHERE old.child_id IN (
                        SELECT child_id FROM {cls._meta.db_table} WHERE parent_id = %s
                    ) AND new_rel.parent_id IS NULL
                )
            """, [node_id, new_parent_id, node_id])

    @classmethod
    def get_descendants(cls, node_id, include_self=True):
        with connection.cursor() as cursor:
            if include_self:
                cursor.execute(f"""
                    SELECT child_id FROM {cls._meta.db_table}
                    WHERE parent_id = %s ORDER BY depth ASC
                """, [node_id])
            else:
                cursor.execute(f"""
                    SELECT child_id FROM {cls._meta.db_table}
                    WHERE parent_id = %s AND depth > 0 ORDER BY depth ASC
                """, [node_id])
            return [row[0] for row in cursor.fetchall()]

    @classmethod
    def get_ancestors(cls, node_id, include_self=True):
        with connection.cursor() as cursor:
            if include_self:
                cursor.execute(f"""
                    SELECT parent_id FROM {cls._meta.db_table}
                    WHERE child_id = %s ORDER BY depth ASC
                """, [node_id])
            else:
                cursor.execute(f"""
                    SELECT parent_id FROM {cls._meta.db_table}
                    WHERE child_id = %s AND depth > 0 ORDER BY depth ASC
                """, [node_id])
            return [row[0] for row in cursor.fetchall()]

    @classmethod
    def get_depth(cls, node_id):
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT MAX(depth) FROM {cls._meta.db_table}
                WHERE child_id = %s
            """, [node_id])
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0

    @classmethod
    def get_level(cls, node_id):
        return cls.get_depth(node_id) + 1

    @classmethod
    @transaction.atomic
    def delete_all(cls):
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {cls._meta.db_table}")

    @classmethod
    @transaction.atomic
    def rebuild_closure(cls, model_cls):
        """
        Пересобрать closure из модели дерева (model_cls), предполагающей поля id и tn_parent_id.
        """
        cls.delete_all()
        with connection.cursor() as cursor:
            cursor.execute(f"""
                WITH RECURSIVE closure_build(parent_id, child_id, depth) AS (
                    SELECT id, id, 0 FROM {model_cls._meta.db_table}
                    UNION ALL
                    SELECT p.tn_parent_id, c.child_id, c.depth + 1
                    FROM {model_cls._meta.db_table} p
                    JOIN closure_build c ON p.id = c.parent_id
                    WHERE p.tn_parent_id IS NOT NULL
                )
                INSERT INTO {cls._meta.db_table} (parent_id, child_id, depth)
                SELECT parent_id, child_id, depth FROM closure_build
            """)
