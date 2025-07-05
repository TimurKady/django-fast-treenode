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
        attrs.setdefault("data-url", reverse("treenode:tree_autocomplete"))
        attrs.setdefault("data-url-children", reverse("treenode:tree_children"))
        attrs["class"] = f"{attrs.get('class', '')} tree-widget".strip()

        model = getattr(self, "model", None)
        if not model and hasattr(self.choices, "queryset"):
            model = self.choices.queryset.model
        elif model is None:
            raise ValueError("TreeWidget: model not passed or not defined")
        attrs["data-model"] = model._meta.label

        return attrs

    def optgroups(self, name, value, attrs=None):
        """
        Override optgroups to return an empty structure.

        The dropdown will be rendered dynamically via JS.
        """
        return []

    def id_for_label(self, id_):
        """Return label for field."""
        return f"{id_}_search"

    def label_from_instance(self, obj):
        """Return instance label."""
        return str(obj)

    def render(self, name, value, attrs=None, renderer=None):
        """Render widget as a hidden input + tree container structure."""
        attrs = self.build_attrs(attrs)
        attrs["name"] = name
        attrs["type"] = "hidden"
        attrs["value"] = str(value) if value else ""

        # If value is set, try to get string representation of instance,
        # otherwise print "Root"
        if str(value).lower() not in ("", "none"):
            model = self.model or self.choices.queryset.model
            instance = model.objects.filter(pk=value).first()
            if instance:
                selected_value = str(instance)
            else:
                selected_value = _("Root")
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
                    <input id="id_parent_search" type="text" class="tree-search" placeholder="{search_placeholder}" />
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
