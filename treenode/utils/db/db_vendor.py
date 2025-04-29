# -*- coding: utf-8 -*-
"""
API-First Support Module.

CRUD and Tree Operations for TreeNode models.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import connection

_vendor = connection.vendor.lower()


def is_postgresql():
    """Return True if DB is PostgreSQL."""
    return _vendor == "postgresql"


def is_mysql():
    """Return True if DB is MySQL."""
    return _vendor == "mysql"


def is_mariadb():
    """Return True if DB is MariaDB."""
    return _vendor == "mariadb"


def is_sqlite():
    """Return True if DB is SQLite."""
    return _vendor == "sqlite"


def is_oracle():
    """Return True if DB is Oracle."""
    return _vendor == "oracle"


def is_mssql():
    """Return True if DB is Microsoft SQL Server."""
    return _vendor in ("microsoft", "mssql")


def get_vendor():
    """Return DB vendor."""
    return _vendor
