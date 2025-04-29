# -*- coding: utf-8 -*-
"""
Custon tags for changelist tamplate.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django import template
from django.contrib.admin.templatetags import admin_list

register = template.Library()


@register.inclusion_tag(
    "admin/treenode_rows.html",
    takes_context=True,
)
def tree_result_list(context, cl):
    """
    Return custom results for change_list.

    Заголовки берём из стандартного admin_list.result_headers(),
    а строки формируем как угодно.
    """
    headers = list(admin_list.result_headers(cl))

    rows = []
    for obj in cl.result_list:
        cells = list(admin_list.items_for_result(cl, obj, None))
        rows.append({
            "attrs": getattr(obj, "row_attrs", ""),
            "cells": cells,
            "form": None,   # поддержка list_editable, если нужно
        })

    return {
        **context.flatten(),
        "headers": headers,
        "rows": rows,
        "num_sorted_fields": sum(
            1 for h in headers if h["sortable"] and h["sorted"]
        ),
    }
