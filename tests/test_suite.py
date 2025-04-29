# -*- coding: utf-8 -*-
"""
Automated tests for TreeNodeModel.
"""

import unittest
from django.db import transaction
from .models import TestModel

PATH_DIGITS = 3


def _set_path(array):
    """Store the path as a zero-padded hex string."""
    return '.'.join(f"{n:0{PATH_DIGITS}X}" for n in array)


class TreeNodeModelTests(unittest.TestCase):
    """Test cases for the TreeNodeModel behavior."""

    def setUp(self):
        # Чистим таблицу перед каждым тестом
        TestNode.objects.all().delete()

    @transaction.atomic
    def test_tree_operations(self):
        """Main test covering tree creation, move, and serialization."""

        # 1️⃣ Create a test tree
        root = TestNode.objects.create(name="root", priority=0)
        node_a = TestNode.objects.create(name="A", parent=root, priority=1)
        node_b = TestNode.objects.create(name="B", parent=root, priority=2)
        node_c = TestNode.objects.create(name="C", parent=node_a, priority=1)
        node_d = TestNode.objects.create(name="D", parent=node_a, priority=2)

        self.assertEqual(TestNode.objects.count(), 5)

        # 2️⃣ Check the saving of `_path`
        path_a = node_a.get_order()
        path_c = node_c.get_order()

        self.assertEqual(node_a.get_depth(), 1)
        self.assertEqual(node_c._depth, 2)
        self.assertTrue(isinstance(path_a, str) and '.' in path_a)
        self.assertTrue(isinstance(path_c, str) and '.' in path_c)

        # 3️⃣ Check ancestors and descendants
        ancestor_ids = set(
            node_c.get_ancestors_queryset().values_list("pk", flat=True))
        self.assertEqual(ancestor_ids, {root.pk, node_a.pk, node_c.pk})

        descendant_ids = set(root.get_descendants_queryset(
            include_self=True).values_list("pk", flat=True))
        self.assertEqual(descendant_ids, {
                         root.pk, node_a.pk, node_b.pk, node_c.pk, node_d.pk})

        # 4️⃣ Move node_c under node_b
        node_c.move_to(node_b)
        self.assertEqual(node_c.parent.pk, node_b.pk)
        self.assertEqual(node_c.get_depth(), node_b.get_depth() + 1)
        self.assertTrue(node_c.get_order().startswith(node_b.get_order() + '.'))
        self.assertEqual(node_c.get_order().count('.'), node_c.get_depth())

        # 5️⃣ Check deletion
        node_a.delete()
        self.assertFalse(TestNode.objects.filter(pk=node_a.pk).exists())
        self.assertTrue(TestNode.objects.filter(pk=node_c.pk).exists())

        # 6️⃣ Check save and load operations
        TestNode.objects.all().delete()
        self.assertFalse(TestNode.objects.exists())

        # Recreate the tree
        root = TestNode.objects.create(name="root", priority=0)
        node_a = TestNode.objects.create(name="A", parent=root, priority=1)
        node_b = TestNode.objects.create(name="B", parent=root, priority=2)
        node_c = TestNode.objects.create(name="C", parent=node_a, priority=1)
        node_d = TestNode.objects.create(name="D", parent=node_a, priority=2)

        original_tree = TestNode.get_tree()
        tree_json = TestNode.get_tree_json()
        tree_data = TestNode.load_tree_json(tree_json)

        TestNode.objects.all().delete()
        self.assertFalse(TestNode.objects.exists())

        TestNode.load_tree(tree_data)
        new_tree = TestNode.get_tree_json()

        # ✅ Checking the integrity of the tree after all operations
        self.assertEqual(root.check_tree_integrity(verbose=False), [])
