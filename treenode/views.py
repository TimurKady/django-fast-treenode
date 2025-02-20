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

Version: 2.0.11
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.http import JsonResponse
from django.views import View
from django.apps import apps
import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _


class TreeNodeAutocompleteView(View):
    """Returns JSON data for Select2 with tree structure."""

    def get(self, request):
        """Get method."""
        q = request.GET.get("q", "")
        model_label = request.GET.get("model")  # Получаем модель

        if not model_label:
            return JsonResponse(
                {"error": "Missing model parameter"},
                status=400
            )

        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )

        queryset = model.objects.filter(name__icontains=q)
        # Sorting
        tn_orders = np.array([obj.tn_order for obj in queryset])
        sorted_indices = np.argsort(tn_orders)
        queryset_list = list(queryset.iterator())
        sorted_queryset = [queryset_list[int(idx)] for idx in sorted_indices]

        results = [
            {
                "id": node.pk,
                "text": node.name,
                "level": node.get_level(),
                "is_leaf": node.is_leaf(),
            }
            for node in sorted_queryset
        ]

        root_option = {
            "id": "",
            "text": _("Root"),
            "level": 0,
            "is_leaf": True,
        }
        results.insert(0, root_option)

        return JsonResponse({"results": results})


class GetChildrenCountView(View):
    """Return the number of children for a given parent node."""

    def get(self, request):
        """Get method."""
        parent_id = request.GET.get("parent_id")
        model_label = request.GET.get("model")  # Получаем модель

        if not model_label or not parent_id:
            return JsonResponse({"error": "Missing parameters"}, status=400)

        try:
            model = apps.get_model(model_label)
        except LookupError:
            return JsonResponse(
                {"error": f"Invalid model: {model_label}"},
                status=400
            )

        try:
            parent_node = model.objects.get(pk=parent_id)
            children_count = parent_node.get_children_count()
        except ObjectDoesNotExist:
            return JsonResponse(
                {"error": "Parent node not found"},
                status=404
            )

        return JsonResponse({"children_count": children_count})
