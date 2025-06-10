# -*- coding: utf-8 -*-
"""
TreeNode Admin Model Class Mixin

Views for AdminModel

Version: 3.0.7
Author: Timur Kady
Email: timurkady@yandex.com
"""

import os
import json
from datetime import datetime
from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.utils import lookup_field
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import path
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache


class AdminMixin(admin.ModelAdmin):
    """Admin Mixin for lazy loading and search in tree."""

    def get_search_help_text(self, request):
        """Get search help text."""
        return getattr(super(), 'get_search_help_text', lambda r: '')(request)

    def get_urls(self):
        """Add custom URLs for AJAX loading and searching."""
        default_urls = super().get_urls()

        custom_urls = [
            path(
                "change_list/",
                self.admin_site.admin_view(self.ajax_changelist_view),
                name="tree_changelist"
            ),
            path(
                "move/",
                self.admin_site.admin_view(self.ajax_move_view),
                name="tree_changelist_move"
            ),
            path(
                "import/",
                self.admin_site.admin_view(self.import_view),
                name="tree_node_import"
            ),
            path("export/",
                 self.admin_site.admin_view(self.export_view),
                 name="tree_node_export"
                 ),
        ]
        return custom_urls + default_urls

    def render_changelist_rows(self, objs: list, request):
        """Rander rows for incert to changelist."""
        list_display = list(self.get_list_display(request))
        checkbox_field_name = ACTION_CHECKBOX_NAME
        if checkbox_field_name not in list_display:
            list_display.insert(0, checkbox_field_name)

        rows = []
        for obj in objs:
            row_data = []
            td_classes = []

            for field in list_display:
                if field == ACTION_CHECKBOX_NAME:
                    checkbox = f'<input type="checkbox" id="action_{obj.pk}" name="{ACTION_CHECKBOX_NAME}" value="{obj.pk}" class="action-select" />'  # noqa: D501
                    row_data.append(mark_safe(checkbox))
                    td_classes.append("action-checkbox")
                    continue

                if callable(field):
                    value = field(obj)
                    field_name = getattr(field, "__name__", "field")
                else:
                    attr, value = lookup_field(field, obj, self)
                    field_name = field

                row_data.append(value)
                td_classes.append(f"field-{field_name}")

            rows.append({
                "node_id": obj.pk,
                "attrs": f'data-node-id="{obj.pk}" data-parent-of="{obj.parent_id or ""}" class="model-{self.model._meta.model_name} pk-{obj.pk}"',  # noqa: D501
                "parent_id": obj.parent_id,
                "cells": list(zip(row_data, td_classes)),
            })
        return rows

    @method_decorator(never_cache)
    def ajax_changelist_view(self, request, extra_context=None):
        """
        Create a default changelist or load child elements via AJAX.

        - If `parent_id` is passed, returns only child rows (HTML).
        - If `q` is passed, returns up to 20 matching rows (HTML).
        - Otherwise, displays the full changelist.
        """
        extra_context = extra_context or {}
        extra_context['import_export_enabled'] = self.import_export
        # Define the show_admin_actions variable in the context
        extra_context['show_admin_actions'] = extra_context.get(
            "show_admin_actions", False)
        parent_id = request.GET.get("parent_id", "")
        query = request.GET.get("q", "")
        expanded = request.GET.get("expanded", "[]")

        if parent_id:
            parent = self.model.objects.filter(pk=parent_id).first()
            rows_list = parent.get_children() if parent else []

        elif query:
            name_field = getattr(self.model, "display_field", "id")
            rows_list = list(self.model.objects.filter(
                Q(**{f"{name_field}__icontains": query})
                | Q(pk__icontains=query)
            ).order_by("_path")[:20])

        elif expanded:
            try:
                expanded_list = json.loads(expanded)
            except ValueError:
                return JsonResponse({"error": _("Bad node list.")}, status=422)
            if expanded_list:
                queryset = self.model.objects.filter(
                    Q(parent__isnull=True) |
                    Q(pk__in=expanded_list) |
                    Q(parent_id__in=expanded_list)
                ).distinct()
            else:
                queryset = self.model.objects.filter(parent__isnull=True)

            rows_list = list(queryset.order_by("_path"))
        else:
            return JsonResponse({"html": ""})

        rows = self.render_changelist_rows(rows_list, request)

        # Take model verbose name
        verbose_name = getattr(self.model._meta, "verbose_name_plural", None) \
            or getattr(self.model._meta, "verbose_name", None) \
            or self.model._meta.object_name

        # Render HTML
        html = render_to_string(
            "treenode/admin/treenode_ajax_rows.html",
            {"rows": rows},
            request=request
        )
        return JsonResponse({"html": html, "label": verbose_name})

    @method_decorator(never_cache)
    def ajax_move_view(self, request, extra_context=None):
        """
        Perform drag-and-drop move operation for a node.

        Moves a node relative to a target node using the specified mode.
        """
        # 1. Extracting parameters
        node_id = request.POST.get("node_id")
        target_id = request.POST.get("target_id")
        mode = request.POST.get("mode")

        if not (node_id and mode):
            return JsonResponse({"error": _("Missing parameters.")}, status=400)

        # 2. Getting objects
        node = self.model.objects.filter(pk=node_id).first()
        if not node or mode not in ("child", "after"):
            return JsonResponse(
                {"error": _(f"Invalid node ({node_id}) or mode ({mode}).")},
                status=422
            )

        # Prepare the target
        if not target_id or target_id == 'null':
            # Insetr like a root
            target_id = None
            target = None
        else:
            target_id = int(target_id)
            target = self.model.objects.filter(pk=target_id).first()

        # 3. Protection from moving into your descendants
        descendants_pks = node.query("descendants", include_self=True)
        if target_id in descendants_pks:
            return JsonResponse({
                "error": _("Cannot move a node into its own descendants.")
            }, status=409)

        # 4. Positioning and moving
        sorting_mode = self.model.sorting_field == 'priority'
        if target:
            position = {
                "after": 'right-sibling' if sorting_mode else 'sorted-sibling',
                "child": 'last-child' if sorting_mode else 'sorted-child'
            }[mode]
        else:
            position = 'first-root' if sorting_mode else 'sorted-root'

        # 5. Adjustments
        if mode == 'after' and node.parent == target:
            # User wants to insert a node after a node-parent
            # print("User wants to insert a node after a node-parent.")
            pass

        # Debug
        # print(mode, "-", position)

        # Moving
        node.move_to(target, position)

        return JsonResponse({
            "message": _("1 node successfully moved")
        }, status=200)

    def import_view(self, request):
        """
        Impoern View.

        Handles file upload and initiates import processing via
        TreeNodeImporter.
        Renders summary and any errors.
        """
        if request.method == "POST":
            file = request.FILES.get("file")
            if not file:
                return HttpResponseBadRequest("Missing file or format")

            filename = file.name
            extension = os.path.splitext(filename)[1].lower().lstrip('.')
            if extension not in ['csv', 'tsv', 'json', 'xlsx', 'yaml']:
                return JsonResponse(
                    {"error": _(f"Invalid file format ({extension}.")},
                    status=200
                )
            importer = self.TreeNodeImporter(self.model, file, extension)
            importer.parse()
            result = importer.import_tree()

            return render(request, "treenode/admin/treenode_import_export.html", {
                "created_count": result.get("created", 0),
                "updated_count": result.get("updated", 0),
                "errors": result.get("errors", []),
                "import_active": True
            })

        return render(
            request,
            "treenode/admin/treenode_import_export.html",
            {"import_active": True}
        )

    def export_view(self, request):
        """
        Export View.

        Handles GET-based export of data in selected format via
        TreeNodeExporter.
        Returns a streaming response for large datasets.
        """
        if request.GET.get("download"):
            fmt = request.GET.get("format", "csv")
            filename = self.model._meta.object_name
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"{filename}-{timestamp}.{fmt}"
            exporter = self.TreeNodeExporter(
                self.model,
                filename=filename,
                fileformat=fmt
            )
            return exporter.process_record()

        return render(
            request,
            "treenode/admin/treenode_import_export.html",
            {"import_active": False}
        )

# The End
