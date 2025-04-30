# tests/test_treenode.py
from django.test import TestCase
from django.db import transaction
from .models import TestNode

PATH_DIGITS = 3


def hex_path(parts):
    """Преобразуем массив индексов в нулепад-hex-строку."""
    return ".".join(f"{n:0{PATH_DIGITS}X}" for n in parts)


class TreeNodeModelTests(TestCase):
    """Проверяем основные операции TreeNodeModel."""

    @classmethod
    def setUpTestData(cls):
        """
        Создаём тестовое дерево один раз на весь класс.
        Django сделает его снимок, и в каждом тесте база
        будет возвращаться в это состояние автоматически.
        """
        cls.root = TestNode.objects.create(name="root", priority=0)
        cls.a = TestNode.objects.create(name="A", parent=cls.root, priority=1)
        cls.b = TestNode.objects.create(name="B", parent=cls.root, priority=2)
        cls.c = TestNode.objects.create(name="C", parent=cls.a, priority=1)
        cls.d = TestNode.objects.create(name="D", parent=cls.a, priority=2)

    # --- 1. Creating nodes -------------------------------------------------

    def test_count_after_creation(self):
        self.assertEqual(TestNode.objects.count(), 5)

    # --- 2. _path and _depth --------------------------------------------------

    def test_path_and_depth_saved(self):
        with self.subTest("Depth values"):
            self.assertEqual(self.a.get_depth(), 1)
            self.assertEqual(self.c.get_depth(), 2)

        with self.subTest("Path format"):
            self.assertIn(".", self.a.get_order())
            self.assertIn(".", self.c.get_order())

    # --- 3. Ancestors and Descendants ------------------------------------------------

    def test_ancestors_and_descendants(self):
        ancestors = set(
            self.c.get_ancestors_queryset().values_list("pk", flat=True)
        )
        expected_anc = {self.root.pk, self.a.pk, self.c.pk}
        self.assertEqual(ancestors, expected_anc)

        descendants = set(
            self.root.get_descendants_queryset(include_self=True)
            .values_list("pk", flat=True)
        )
        expected_desc = {
            self.root.pk, self.a.pk, self.b.pk, self.c.pk, self.d.pk
        }
        self.assertEqual(descendants, expected_desc)

    # --- 4. Moving a node ------------------------------------------------

    def test_move_node(self):
        # перемещаем c под b и проверяем
        with transaction.atomic():
            self.c.move_to(self.b)

        self.c.refresh_from_db()
        self.assertEqual(self.c.parent_id, self.b.pk)
        self.assertEqual(self.c.get_depth(), self.b.get_depth() + 1)
        self.assertTrue(
            self.c.get_order().startswith(f"{self.b.get_order()}.")
        )
        self.assertEqual(self.c.get_order().count("."), self.c.get_depth())

    # --- 5. Removing a node ---------------------------------------------------

    def test_delete_subtree(self):
        self.a.delete()
        self.assertFalse(TestNode.objects.filter(pk=self.a.pk).exists())
        self.assertTrue(TestNode.objects.filter(pk=self.c.pk).exists())
