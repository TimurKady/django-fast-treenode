# -*- coding: utf-8 -*-
"""
Aid Utility Module

This module provides various helper functions.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.utils.safestring import mark_safe


def object_to_content(obj):
    """Convert object data to widget options string."""
    level = obj.get_depth()
    icon = "📄 " if obj.is_leaf() else "📁 "
    obj_str = str(obj)
    content = (
        f'<span class="treenode-option" style="padding-left: {level * 1.5}em;">'
        f'{icon}{obj_str}</span>'
    )
    return mark_safe(content)


def to_base16(num):
    """
    Convert an integer to a base16 string.

    For example: 10 -> 'A', 11 -> 'B', etc.
    """
    digits = "0123456789ABCDEF"

    if num == 0:
        return '0'
    sign = '-' if num < 0 else ''
    num = abs(num)
    result = []
    while num:
        num, rem = divmod(num, 16)
        result.append(digits[rem])
    return sign + ''.join(reversed(result))

# The End
