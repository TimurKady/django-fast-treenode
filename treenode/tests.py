from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.template import Context
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase

from tests.models import TestModel
from treenode.admin.mixin import AdminMixin
from treenode.templatetags.treenode_admin import tree_result_list


class TestAdminMixin(AdminMixin):
    """Admin class for testing row rendering helpers."""


class AdminRowsRenderTests(TestCase):
    """Tests for admin row attrs in template tag and AJAX helper."""

    @classmethod
    def setUpTestData(cls):
        """Prepare a tiny tree for row rendering checks."""
        cls.root = TestModel.objects.create(name="root-row", priority=0)
        cls.child = TestModel.objects.create(
            name="child-row", parent=cls.root, priority=1
        )

    def setUp(self):
        """Create request and admin instances for each test."""
        self.factory = RequestFactory()
        self.request = self.factory.get("/admin/tests/testmodel/")
        self.admin = TestAdminMixin(TestModel, AdminSite())

    def test_admin_mixin_rows_use_parent_id_attr(self):
        """Ensure helper rows contain data-parent-id and data-depth attrs."""
        rows = self.admin.render_changelist_rows([self.child], self.request)

        attrs = rows[0]["attrs"]
        self.assertIn('data-node-id="{}"'.format(self.child.pk), attrs)
        self.assertIn('data-parent-id="{}"'.format(self.root.pk), attrs)
        self.assertIn('data-depth="{}"'.format(self.child.get_depth()), attrs)
        self.assertNotIn("data-parent-of", attrs)

    def test_ajax_rows_template_uses_parent_id_attr(self):
        """Ensure AJAX row template renders data-parent-id instead of old attr."""
        html = render_to_string(
            "treenode/admin/treenode_ajax_rows.html",
            {
                "rows": [
                    {
                        "node_id": self.child.pk,
                        "parent_id": self.root.pk,
                        "depth": self.child.get_depth(),
                        "cells": [("value", "field-name")],
                    }
                ]
            },
        )

        self.assertIn('data-node-id="{}"'.format(self.child.pk), html)
        self.assertIn('data-parent-id="{}"'.format(self.root.pk), html)
        self.assertIn('data-depth="{}"'.format(self.child.get_depth()), html)
        self.assertNotIn("data-parent-of", html)

    def test_tree_result_list_contains_expected_attrs(self):
        """Ensure main template tag rows follow node/parent/depth attrs schema."""
        cl = SimpleNamespace(actions=False, result_list=[self.child])
        headers = [
            {
                "text": "Name",
                "class_attrib": "",
                "sortable": False,
                "sorted": False,
            }
        ]

        with patch(
            "treenode.templatetags.treenode_admin.admin_list.result_headers",
            return_value=headers,
        ), patch(
            "treenode.templatetags.treenode_admin.admin_list.items_for_result",
            return_value=['<td class="field-name">child-row</td>'],
        ):
            result = tree_result_list(Context({}), cl)

        attrs = result["rows"][0]["attrs"]
        self.assertIn('data-node-id="{}"'.format(self.child.pk), attrs)
        self.assertIn('data-parent-id="{}"'.format(self.root.pk), attrs)
        self.assertIn('data-depth="{}"'.format(self.child.get_depth()), attrs)
        self.assertNotIn("data-parent-of", attrs)


# The End

