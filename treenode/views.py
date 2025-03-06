# -*- coding: utf-8 -*-
"""
TreeNode Views Module

This module provides API views for handling AJAX requests related to
tree-structured data in Django. It supports Select2 autocomplete
and retrieving child node counts.

Features:
- `TreeNodeAutocompleteView`: Returns JSON data for Select2 with hierarchical
   structure.
- `GetChildrenCountView`: Retrieves the number of children for a given
   parent node.
- Uses optimized QuerySets for efficient database queries.
- Handles validation and error responses gracefully.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.apps import apps
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View

import logging

logger = logging.getLogger(__name__)


class TreeNodeAutocompleteView(View):
    """
    Return JSON data for Select2 with tree structure.

    Lazy load tree nodes for Select2 scrolling with reference node support.
    """

    def get(self, request):
        """
        Process an AJAX request to lazily load tree nodes.

        Operation logic:
        """
        # Search Processing
        q = request.GET.get("q", "")
        if q:
            return self.search(request)

        # Model extracting
        model_label = request.GET.get("model")
        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )

        # select_id not specified
        queryset_list = model.get_roots()

        select_id = request.GET.get("select_id", "")
        if select_id:
            select = model.objects.filter(pk=select_id).first()
            if not select:
                return JsonResponse(
                    {"error": f"Invalid select_id: {select_id}"},
                    status=400
                )
            breadcrumbs = select.get_breadcrumbs()
            # Delete self
            del breadcrumbs[-1]
            for pk in breadcrumbs:
                parent = model.model.objects.filter(pk=pk).first()
                children = parent.get_children()
                queryset_list.extend(children)

        nodes = model._sort_node_list(queryset_list)
        # Generate a response
        results = [
            {
                "id": node.pk,
                "text": str(node),
                "level": node.get_depth(),
                "is_leaf": node.is_leaf(),
            }
            for node in nodes
        ]
        # Add the "Root" option to the top of the list
        root_option = {
            "id": "",
            "text": _("Root"),
            "level": 0,
            "is_leaf": True,
        }
        results.insert(0, root_option)

        response_data = {"results": results}
        return JsonResponse(response_data)

    def search(self, request):
        """Search processing."""
        # Chack search query
        q = request.GET.get("q", "")
        if not q:
            return JsonResponse({"results": []})

        # Model extracting
        model_label = request.GET.get("model")
        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )

        # Search
        params = {}
        treenode_field = model.treenode_display_field
        if not treenode_field:
            return {"results": ""}

        params[f"{treenode_field}__icontains"] = q
        queryset = model.objects.filter(**params)[:15]
        queryset_list = list(queryset)
        nodes = model._sort_node_list(queryset_list)
        results = [
            {
                "id": node.pk,
                "text": node.name,
                "level": node.get_depth(),
                "is_leaf": node.is_leaf(),
            }
            for node in nodes
        ]
        return JsonResponse({"results": results})


class ChildrenView(View):
    """Return JSON data for Select2 with node children."""

    def get(self, request):
        """Process an AJAX request to load node children."""
        # Get reference_id
        reference_id = request.GET.get("reference_id", "")
        if not reference_id:
            return JsonResponse({"results": []})

        # Model extracting
        model_label = request.GET.get("model")
        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )
        obj = model.objects.filter(pk=reference_id).first()
        if not obj:
            return JsonResponse(
                {"error": f"Invalid reference_id: {reference_id}"},
                status=400
            )

        if obj.is_leaf():
            return JsonResponse({"results": []})

        queryset_list = obj.get_children()
        nodes = model._sort_node_list(queryset_list)
        results = [
            {
                "id": node.pk,
                "text": node.name,
                "level": node.get_depth(),
                "is_leaf": node.is_leaf(),
            }
            for node in nodes
        ]
        return JsonResponse({"results": results})


# The End
