# -*- coding: utf-8 -*-
"""
Custom tags for changelist template.

Version: 3.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django import template
from django.contrib.admin.templatetags import admin_list
from django.utils.html import format_html, mark_safe

register = template.Library()


@register.inclusion_tag("treenode/admin/treenode_rows.html", takes_context=True)
def tree_result_list(context, cl):
    """Get result list."""
    headers = list(admin_list.result_headers(cl))

    # Add a checkbox title manually if it is missing
    if cl.actions and not any("action-checkbox-column" in h["class_attrib"] for h in headers):
        headers.insert(0, {
            "text": "",
            "class_attrib": ' class="action-checkbox-column"',
            "sortable": False
        })

    rows = []

    for obj in cl.result_list:
        cells = list(admin_list.items_for_result(cl, obj, None))

        # Insert checkbox manually
        checkbox = format_html(
            '<td class="action-checkbox">'
            '<input type="checkbox" name="_selected_action" value="{}" class="action-select" /></td>',
            obj.pk
        )
        cells.insert(0, checkbox)

        # Replace the toggle cell (3rd after inserting checkbox and move)
        is_leaf = getattr(obj, "is_leaf", lambda: True)()
        toggle_html = format_html(
            '<td class="field-toggle">{}</td>',
            format_html(
                '<button class="treenode-toggle" data-node-id="{}">►</button>',
                obj.pk
            ) if not is_leaf else mark_safe('<div class="treenode-space">&nbsp;</div>')
        )
        if len(cells) >= 3:
            cells.pop(2)
        cells.insert(2, toggle_html)

        depth = getattr(obj, "get_depth", lambda: 0)()
        parent_id = getattr(obj, "parent_id", "")
        is_root = not parent_id

        classes = ["treenode-row"]
        if is_root:
            classes.append("treenode-root")
        else:
            classes.append("treenode-hidden")

        row_attrs = {
            "class": " ".join(classes),
            "data-node-id": obj.pk,
            "data-parent-id": parent_id or "",
            "data-depth": depth,
        }

        rows.append({
            "attrs": " ".join(f'{k}="{v}"' for k, v in row_attrs.items()),
            "cells": cells,
            "form": None,
            "is_leaf": is_leaf,
            "node_id": obj.pk,
        })

    return {
        **context.flatten(),
        "headers": headers,
        "rows": rows,
        "num_sorted_fields": sum(
            1 for h in headers if h["sortable"] and h["sorted"]
        ),
    }
