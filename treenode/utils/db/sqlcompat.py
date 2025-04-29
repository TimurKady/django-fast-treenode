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

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

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
        """Convert integer to hexadecimal string."""
        if is_sqlite():
            return f"printf('%x', {value})"
        else:
            return f"TO_HEX({value})"

    @staticmethod
    def lpad(value, length, char=TREENODE_PAD_CHAR):
        """Pad string to the specified length."""
        if is_sqlite():
            return (f"substr(replace(hex(zeroblob({length})), '00', {char}), "
                    f"1, {length} - length({value})) || {value}")
        else:
            return f"LPAD({value}, {length}, {char})"

# The End
