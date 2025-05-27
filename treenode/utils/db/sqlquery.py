# -*- coding: utf-8 -*-
"""
SQL Queue Class.

SQL query queue supporting Query and (sql, params).

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from __future__ import annotations
from django.db import connections, connection, DEFAULT_DB_ALIAS
from typing import Union, Tuple, List
from django.db.models.sql import Query


class SQLQueue:
    """SQL Queue Class."""

    def __init__(self, using: str = DEFAULT_DB_ALIAS):
        """Init Queue."""
        self.using = using
        self._items: List[Tuple[str, list]] = []

    def append(self, item: Union[Query, Tuple[str, list]]):
        """
        Add a query to the queue.

        Supports:
        - Django Query: model.objects.filter(...).query
        - tuple (sql, params)
        """
        if isinstance(item, tuple):
            sql, params = item
            if not isinstance(sql, str) or not isinstance(params, (list, tuple)):  # noqa: D501
                raise TypeError("Ожидается (sql: str, params: list | tuple)")
            self._items.append((sql, list(params)))

        elif isinstance(item, Query):
            sql, params = item.as_sql(connection)
            self._items.append((sql, params))

        else:
            raise TypeError("Expected either Query or (sql, params)")

    def flush(self):
        """
        Execute all requests from the queue and clear it.

        flush() is called manually.
        """
        if not self._items:
            return

        # print("sqlq: ", self._items)

        conn = connections[self.using]
        with conn.cursor() as cursor:
            for sql, params in self._items:
                try:
                    cursor.execute(sql, params)
                except Exception as e:
                    print(">>> SQLQueue error:", e)
                    raise
        self._items.clear()


# The End
