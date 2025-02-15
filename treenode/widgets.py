# -*- coding: utf-8 -*-
"""
TreeNode Widgets Module

This module defines custom form widgets for handling hierarchical data
within Django's admin interface. It includes a Select2-based widget
for tree-structured data selection.

Features:
- `TreeWidget`: A custom Select2 widget that enhances usability for
  hierarchical models.
- Automatically fetches hierarchical data via AJAX.
- Supports dynamic model binding for reusable implementations.
- Integrates with Django’s form system.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django import forms


class TreeWidget(forms.Select):
    """Custom Select2 widget for hierarchical data."""

    class Media:
        """Mrta class."""

        css = {
            "all": (
                "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css",
                "treenode/css/tree_widget.css",
            )
        }
        js = (
            "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js",
            "treenode/js/tree_widget.js",
        )

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Add attributes for Select2 integration."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-url", "/treenode/tree-autocomplete/")
        existing_class = attrs.get("class", "")
        attrs["class"] = f"{existing_class} tree-widget".strip()
        if "placeholder" in attrs:
            del attrs["placeholder"]

        # Принудительно передаём `model`
        if "data-forward" not in attrs:
            try:
                model = self.choices.queryset.model
                label = model._meta.app_label
                model_name = model._meta.model_name
                model_label = f"{label}.{model_name}"
                attrs["data-forward"] = f'{{"model": "{model_label}"}}'
            except Exception:
                attrs["data-forward"] = '{"model": ""}'

        return attrs


# The End
