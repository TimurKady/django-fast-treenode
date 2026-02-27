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


class AdminMoveViewTests(TestCase):
    """Tests for ajax_move_view parameter contract and validations."""

    @classmethod
    def setUpTestData(cls):
        """Build a small fixture tree for move-view tests."""
        cls.root = TestModel.objects.create(name="root-move", priority=0)
        cls.left = TestModel.objects.create(
            name="left", parent=cls.root, priority=1
        )
        cls.right = TestModel.objects.create(
            name="right", parent=cls.root, priority=2
        )
        cls.leaf = TestModel.objects.create(
            name="leaf", parent=cls.left, priority=1
        )

    def setUp(self):
        """Prepare request factory and admin wrapper."""
        self.factory = RequestFactory()
        self.admin = TestAdminMixin(TestModel, AdminSite())

    def test_ajax_move_requires_anchor_for_before_after(self):
        """Return validation error when before/after has no anchor_id."""
        request = self.factory.post(
            "/admin/tests/testmodel/move/",
            {
                "node_id": self.left.pk,
                "anchor_id": "",
                "position": "before",
            },
        )
        response = self.admin.ajax_move_view(request)

        self.assertEqual(response.status_code, 422)

    def test_ajax_move_rejects_move_to_own_subtree(self):
        """Reject move when anchor is inside moved node subtree."""
        request = self.factory.post(
            "/admin/tests/testmodel/move/",
            {
                "node_id": self.left.pk,
                "anchor_id": self.leaf.pk,
                "position": "inside-last",
            },
        )
        response = self.admin.ajax_move_view(request)

        self.assertEqual(response.status_code, 409)

    def test_ajax_move_inside_last_moves_under_anchor(self):
        """Move node into anchor as the last child for inside-last."""
        request = self.factory.post(
            "/admin/tests/testmodel/move/",
            {
                "node_id": self.leaf.pk,
                "anchor_id": self.right.pk,
                "position": "inside-last",
            },
        )
        response = self.admin.ajax_move_view(request)

        self.leaf.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.leaf.parent_id, self.right.pk)


# The End

