# -*- coding: utf-8 -*-
"""
TreeNode Admin Model Class

Version: 3.0.7
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.contrib import admin
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .changelist import TreeNodeChangeList
from .mixin import AdminMixin
from ..forms import TreeNodeForm
from ..widgets import TreeWidget
from .importer import TreeNodeImporter
from .exporter import TreeNodeExporter

import logging

logger = logging.getLogger(__name__)


class TreeNodeModelAdmin(AdminMixin, admin.ModelAdmin):
    """Admin for TreeNodeModel."""

    # Режимы отображения
    TREENODE_DISPLAY_MODE_ACCORDION = 'accordion'
    TREENODE_DISPLAY_MODE_BREADCRUMBS = 'breadcrumbs'
    TREENODE_DISPLAY_MODE_INDENTATION = 'indentation'
    treenode_display_mode = TREENODE_DISPLAY_MODE_ACCORDION

    form = TreeNodeForm
    importer_class = None
    exporter_class = None
    ordering = []
    list_per_page = 1000

    formfield_overrides = {
        models.ForeignKey: {'widget': TreeWidget()},
    }

    change_list_template = "treenode/admin/treenode_changelist.html"
    import_export = True

    class Media:
        """Meta Class."""

        css = {"all": (
            "css/treenode_admin.css",
            "vendors/jquery-ui/jquery-ui.css",
        )}
        js = (
            "vendors/jquery-ui/jquery-ui.js",
            # "js/lz-string.min.js",
            "js/treenode_admin.js",
        )

    def __init__(self, model, admin_site):
        """Init method."""
        super().__init__(model, admin_site)

        if not self.list_display:
            self.list_display = [field.name for field in model._meta.fields]

        self.TreeNodeImporter = self.importer_class or TreeNodeImporter
        self.TreeNodeExporter = self.exporter_class or TreeNodeExporter

    def drag(self, obj):
        """Drag and drop сolumn."""
        return mark_safe('<span class="treenode-drag-handle">&#9776;</span>')

    drag.short_description = _("Move")

    def toggle(self, obj):
        """Toggle column."""
        if obj.get_children_count() > 0:
            return mark_safe(
                f'<button class="treenode-toggle" data-node-id="{obj.pk}">►</button>'  # noqa
            )
        return mark_safe('<div class="treenode-space">&nbsp;</div>')

    toggle.short_description = _("Expand")

    def _get_treenode_field_display(self, request, obj):
        """Return HTML for the tree node in list view."""
        level = obj.get_depth()
        edit_url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=[obj.pk]
        )

        if self.treenode_display_mode == self.TREENODE_DISPLAY_MODE_ACCORDION:
            icon = "📄 " if obj.is_leaf() else "📁 "
            content = (
                f'<span style="padding-left: {level * 1.5}em;">'
                f'{icon}<a href="{edit_url}">{str(obj)}</a></span>'
            )
        elif self.treenode_display_mode == self.TREENODE_DISPLAY_MODE_BREADCRUMBS:
            breadcrumbs = obj.get_ancestors(include_self=True)
            model_label = obj._meta.app_label
            model_name = obj._meta.model_name
            href = f"admin:{model_label}_{model_name}_change"

            display_attr = getattr(obj, 'display_field', 'id')

            records = [
                (
                    getattr(item, display_attr, item.pk),
                    reverse(href, args=[item.pk]),
                )
                for item in breadcrumbs
            ]

            content = " / ".join([
                f'<a href="{url}">{escape(label)}</a>'
                for label, url in records
            ])

        elif self.treenode_display_mode == self.TREENODE_DISPLAY_MODE_INDENTATION:  # noqa
            indent = "&mdash;" * level
            content = f'{indent}<a href="{edit_url}">{str(obj)}</a>'
        else:
            content = f'<a href="{edit_url}">{str(obj)}</a>'

        html = (
            f'<div class="treenode-wrapper" '
            f'data-treenode-pk="{obj.pk}" '
            f'data-treenode-depth="{level}" '
            f'data-treenode-parent="{obj.parent_id or ""}">'
            f'<span class="treenode-content">{content}</span>'
            f'</div>'
        )
        return mark_safe(html)

    def get_list_display(self, request):
        """Generate list_display dynamically with tree-aware columns."""
        # Define callable that replaces display field with tree field
        def treenode_field(obj):
            return self._get_treenode_field_display(request, obj)
        treenode_field.short_description = self.model._meta.verbose_name

        display_field = getattr(self.model, 'display_field', '__str__')

        user_list_display = list(super().get_list_display(request))
        # If the list is empty or only contains __str__, replace it entirely
        if not user_list_display or user_list_display == ['__str__']:
            user_list_display = [treenode_field]
        else:
            try:
                pos = user_list_display.index(display_field)
                user_list_display.pop(pos)
                user_list_display.insert(pos, treenode_field)
            except ValueError:
                user_list_display.insert(0, treenode_field)

        return (self.drag, self.toggle) + tuple(user_list_display)

    def get_list_display_links(self, request, list_display):
        """Get display list links."""
        return ('treenode_field',)

    def get_queryset(self, request):
        """By default: only root nodes, unless searching or editing."""
        qs = super().get_queryset(request)

        if request.GET.get("q"):
            return qs

        resolved = request.resolver_match
        if resolved and resolved.url_name.endswith("_change"):
            return qs

        return qs.filter(parent__isnull=True)

    def get_form(self, request, obj=None, **kwargs):
        """Get Form method."""
        form = super().get_form(request, obj, **kwargs)
        if "parent" in form.base_fields:
            form.base_fields["parent"].widget = TreeWidget()
        return form

    def get_search_fields(self, request):
        """Get search fields."""
        return [getattr(self.model, 'treenode_display_field', 'id')]

    def get_changelist(self, request, **kwargs):
        """Get ChangeList Class."""
        return TreeNodeChangeList

    def get_ordering(self, request):
        """Get ordering."""
        return None

    def changelist_view(self, request, extra_context=None):
        """Changelist View."""
        extra_context = extra_context or {}
        # TODO
        extra_context['import_export_enabled'] = self.import_export
        extra_context['num_sorted_fields'] = len(self.get_ordering(request) or [])  # noqa: D501

        response = super().changelist_view(request, extra_context=extra_context)

        # If response is a redirect, then there is no point in updating
        # ChangeList
        if isinstance(response, HttpResponseRedirect):
            return response

        ChangeListClass = self.get_changelist(request)
        cl = ChangeListClass(
            request,
            self.model,
            self.list_display,
            self.list_display_links,
            self.list_filter,
            self.date_hierarchy,
            self.search_fields,
            self.list_select_related,
            self.list_per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
            self.get_sortable_by(request),
            self.get_search_help_text(request),
        )

        cl.get_results(request)
        cl.result_list = self.render_changelist_rows(cl.result_list, request)

        return response

    def get_list_per_page(self, request):
        """Get list per page."""
        return 999999


# The End
