# -*- coding: utf-8 -*-
"""
TreeNode Widgets Module

This module defines a custom form widget for handling hierarchical data
within Django's admin interface. It replaces the standard <select> dropdown
with a fully customizable tree selection UI.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import json
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class TreeWidget(forms.Widget):
    """Custom widget for hierarchical tree selection."""

    class Media:
        """Meta class to define required CSS and JS files."""

        css = {"all": ("treenode/css/tree_widget.css",)}
        js = ("treenode/js/tree_widget.js",)

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build attributes for the widget."""
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-url", reverse("tree_autocomplete"))
        attrs.setdefault("data-url-children", reverse("tree_children"))
        attrs["class"] = f"{attrs.get('class', '')} tree-widget".strip()

        if "data-forward" not in attrs:
            model = getattr(self, "model", None)

            if not model and hasattr(self.choices, "queryset"):
                model = self.choices.queryset.model
            if model is None:
                raise ValueError("TreeWidget: model not passed or not defined")

            try:
                forward_data = json.dumps({"model": model._meta.label})
                attrs["data-forward"] = forward_data.replace('"', "&quot;")
            except AttributeError as e:
                raise ValueError("TreeWidget: invalid Django model") from e

        if self.choices:
            try:
                current_value = self.value()
                if current_value:
                    attrs["data-selected"] = str(current_value)
            except Exception:
                pass

        return attrs

    def optgroups(self, name, value, attrs=None):
        """
        Override optgroups to return an empty structure.

        The dropdown will be rendered dynamically via JS.
        """
        return []

    def render(self, name, value, attrs=None, renderer=None):
        """Render widget as a hidden input + tree container structure."""

        attrs = self.build_attrs(attrs)
        attrs["name"] = name
        attrs["type"] = "hidden"
        if value:
            attrs["value"] = str(value)

        # If value is set, try to get string representation of instance,
        # otherwise print "Root"
        if value not in [None, "", "None"]:
            try:
                from django.apps import apps
                # Define the model: first self.model if it is defined,
                # otherwise via choices
                model = getattr(self, "model", None)
                if model is None and hasattr(self, "choices") and getattr(self.choices, "queryset", None):
                    model = self.choices.queryset.model
                if model is not None:
                    instance = model.objects.get(pk=value)
                    selected_value = str(instance)
                else:
                    selected_value = str(value)
            except Exception:
                selected_value = str(value)
        else:
            selected_value = _("Root")

        # Remove the 'tree-widget' class from the input so it doesn't interfere
        # with container initialization
        if "class" in attrs:
            attrs["class"] = " ".join(
                [cl for cl in attrs["class"].split() if cl != "tree-widget"])

        html = """
        <div class="tree-widget">
            <div class="tree-widget-display">
                <span class="selected-node">{selected_value}</span>
                <span class="tree-dropdown-arrow">▼</span>
            </div>
            <input {attrs} />
            <div class="tree-widget-dropdown">
                <div class="tree-search-wrapper">
                    <span class="tree-search-icon">&#x1F50E;&#xFE0E;</span>
                    <input type="text" class="tree-search" placeholder="{search_placeholder}" />
                    <button type="button" class="tree-search-clear">&times;</button>
                </div>
                <ul class="tree-list"></ul>
            </div>
        </div>
        """.format(
            attrs=" ".join(f'{key}="{val}"' for key, val in attrs.items()),
            search_placeholder=_("Search node..."),
            selected_value=selected_value
        )

        return mark_safe(html)


# The End
