# -*- coding: utf-8 -*-
"""
Base36 Utility Module

This module provides a utility function for converting integers
to Base36 string representation.

Features:
- Converts integers into a more compact Base36 format.
- Maintains lexicographic order when padded with leading zeros.
- Supports negative numbers.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


def to_base36(num):
    """
    Convert an integer to a base36 string.

    For example: 10 -> 'A', 35 -> 'Z', 36 -> '10', etc.
    """
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if num == 0:
        return '0'
    sign = '-' if num < 0 else ''
    num = abs(num)
    result = []
    while num:
        num, rem = divmod(num, 36)
        result.append(digits[rem])
    return sign + ''.join(reversed(result))

# The End
