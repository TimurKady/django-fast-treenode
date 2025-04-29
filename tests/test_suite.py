from django.test import TestCase
from .models import TestModel


class TreeNodeModelTests(TestCase):
    def setUp(self):
        # Чистим базу
        TestModel.objects.all().delete()

        # Строим дерево вручную
        self.root = TestModel.objects.create(name="root", priority=0)
        self.a = TestModel.objects.create(
            name="A", parent=self.root, priority=1)
        self.b = TestModel.objects.create(
            name="B", parent=self.root, priority=2)
        self.c = TestModel.objects.create(name="C", parent=self.a, priority=1)
        self.d = TestModel.objects.create(name="D", parent=self.a, priority=2)
        self.e = TestModel.objects.create(name="E", parent=self.b, priority=1)

        # Обновляем дерево
        path_a = self.a.get_order()
        path_c = self.c.get_order()
        self.root._update_path(None)

    def test_tree_operations(self):
        # Проверка целостности дерева
        self.assertEqual(self.root.check_tree_integrity(verbose=False), [])
