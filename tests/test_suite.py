from django.test import TestCase
from .models import TestModel


class TreeNodeModelTests(TestCase):
    def setUp(self):
        # Cleaning the base
        TestModel.objects.all().delete()

        # Building a tree by hand
        self.root = TestModel.objects.create(name="root", priority=0)
        self.a = TestModel.objects.create(
            name="A", parent=self.root, priority=1)
        self.b = TestModel.objects.create(
            name="B", parent=self.root, priority=2)
        self.c = TestModel.objects.create(name="C", parent=self.a, priority=1)
        self.d = TestModel.objects.create(name="D", parent=self.a, priority=2)
        self.e = TestModel.objects.create(name="E", parent=self.b, priority=1)

        # Обновляем дерево — вручную
        self.root.update_path(recursive=True)

    def test_tree_operations(self):
        # Integrity check
        self.assertEqual(self.root.check_tree_integrity(verbose=False), [])

        # Check get_descendant_pks
        descendants = set(self.root.get_descendant_pks(include_self=False))
        expected = {self.a.pk, self.b.pk, self.c.pk, self.d.pk, self.e.pk}
        self.assertEqual(descendants, expected)

        # Check serialization/deserialization
        tree_data = TestModel.get_tree_json()
        TestModel.objects.all().delete()
        TestModel.load_tree(tree_data)
