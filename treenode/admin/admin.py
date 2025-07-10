# -*- coding: utf-8 -*-
"""
TreeNode Admin Model Class

Modified admin panel for django-fast-treenode. Solves the following problems:
- Set list_per_page = 10000 to display all elements at once.
- Hidden standard pagination via CSS
- Disabled counting the total number of elements to speed up loading
- Accordion works regardless of the display mode
Two modes are supported:
- Indented - with indents and icons
- Breadcrumbs - with breadcrumbs
All modes have links to editing objects.

- Expand buttons for nodes with children

Additional features:
- Control panel with "Expand All" / "Collapse All" buttons
- Saving the state of the tree between page transitions
- Smooth animations when expanding/collapsing
- Counting the total number of nodes in the tree
- Recursive hiding of grandchildren when collapsing the parent

Version: 3.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

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
    treenode_display_mode = TREENODE_DISPLAY_MODE_ACCORDION

    form = TreeNodeForm
    importer_class = None
    exporter_class = None
    ordering = []
    change_list_template = "treenode/admin/treenode_changelist.html"
    import_export = True

    class Media:
        """Meta Class."""

        css = {"all": (
            "treenode/css/treenode_admin.css",
            "treenode/vendors/jquery-ui/jquery-ui.css",
        )}
        js = (
            "treenode/vendors/jquery-ui/jquery-ui.js",
            # "treenode/js/lz-string.min.js",
            "treenode/js/treenode_admin.js",
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

    def get_changelist(self, request, **kwargs):
        """Get changelist."""
        ChangeList = super().get_changelist(request, **kwargs)

        class NoPaginationChangeList(ChangeList):
            """Suppress pagination."""

            def get_results(self, request):
                """Get result."""
                super().get_results(request)
                self.paginator.show_all = True
                self.result_count = len(self.result_list)
                self.full_result_count = len(self.result_list)
                self.can_show_all = False
                self.multi_page = False
                self.actions = self.model_admin.get_actions(request)

        return NoPaginationChangeList

    def get_changelist_instance(self, request):
        """
        Get changelist instance.

        Make sure our custom ChangeList is used without pagination.
        """
        ChangeList = self.get_changelist(request)

        return ChangeList(
            request,
            self.model,
            self.get_list_display(request),
            self.get_list_display_links(
                request,
                self.get_list_display(request)
            ),
            self.get_list_filter(request),
            self.date_hierarchy,
            self.search_fields,
            self.list_select_related,
            self.list_per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
            sortable_by=self.get_sortable_by(request),
            search_help_text=self.get_search_help_text(request),
        )

    def get_queryset(self, request):
        """Get queryset."""
        qs = super().get_queryset(request)
        return qs.select_related('parent')\
            .prefetch_related('children')\
            .order_by('_path')

    def get_list_display(self, request):
        """Get list_display."""
        def treenode_field(obj):
            return self._get_treenode_field_display(request, obj)

        description = str(self.model._meta.verbose_name)
        treenode_field.short_description = description

        return (self.drag, self.toggle, treenode_field)

    def get_form(self, request, obj=None, **kwargs):
        """Get Form method."""
        form = super().get_form(request, obj, **kwargs)
        if "parent" in form.base_fields:
            form.base_fields["parent"].widget = TreeWidget()
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Use TreeWidget only for 'parent' field."""
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == "parent":
            related = getattr(db_field.remote_field, "model", None)
            if related and issubclass(related, TreeNodeModel):
                formfield.widget = TreeWidget()
                formfield.widget.model = related
        return formfield


    def get_search_fields(self, request):
        """Get search fields."""
        return [getattr(self.model, 'display_field', 'id') or 'id']

    def _get_treenode_field_display(self, request, obj):
        """
        Generate HTML to display tree nodes.

        Depending on the selected display mode (accordion or breadcrumbs),
        do the following:
        - For accordion mode: add indents and icons.
        - For breadcrumbs mode: display breadcrumb path.
        """
        level = obj.get_depth()
        display_field = getattr(obj, "display_field", None)
        edit_url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=[obj.pk]
        )
        icon = ""
        text = ""
        padding = ""
        closing = ""

        if self.treenode_display_mode == self.TREENODE_DISPLAY_MODE_ACCORDION:
            icon = "📄 " if obj.is_leaf() else "📁 "
            text = getattr(obj, display_field, str(obj))
            padding = f'<span style="padding-left: {level * 1.5}em;">'
            closing = "</span>"
        elif self.treenode_display_mode == self.TREENODE_DISPLAY_MODE_BREADCRUMBS:  # noqa
            if display_field:
                breadcrumbs = obj.get_breadcrumbs(attr=display_field)
            else:
                breadcrumbs = [str(item) for item in obj.get_ancestors()]

            text = "/" + "/".join([escape(label) for label in breadcrumbs])

        content = f'{padding}{icon}<a href="{edit_url}">{escape(text)}</a>{closing}'  # noqa
        return mark_safe(content)

    def get_list_per_page(self, request):
        """Get list per page."""
        return 999999

# The End
