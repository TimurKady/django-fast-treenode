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

        # Проверка получения потомков
        descendant_names = TestModel.objects.filter(
            pk__in=self.root.get_descendant_pks(include_self=False)
        ).values_list("name", flat=True)

        self.assertEqual(set(descendant_names), {"A", "B", "C", "D", "E"})

        # Сериализация
        tree_data = TestModel.get_tree_json()

        # Удаляем всё и восстанавливаем дерево
        TestModel.objects.all().delete()
        TestModel.load_tree(tree_data)

        # Проверка целостности после восстановления
        new_root = TestModel.objects.get(name="root")
        self.assertEqual(new_root.check_tree_integrity(verbose=False), [])

        restored_names = TestModel.objects.filter(
            pk__in=new_root.get_descendant_pks(include_self=False)
        ).values_list("name", flat=True)

        self.assertEqual(set(restored_names), {"A", "B", "C", "D", "E"})
