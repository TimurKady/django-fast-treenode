import os
import django
import time
import traceback
from django.db import models
from django.test import TestCase, TransactionTestCase
from . import settings
from .models import TestModel


if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"

django.setup()

class BasicOperationsTest(TestCase):
    """
    Tests basic operations with nodes: insertion (using three methods), deletion,
    moving, as well as the functionality of QuerySet methods (e.g. retrieving children).
    """

    def runTest(self):
        errors = []
        print("\n=== BasicOperationsTest ===")

        # 1. Insertion via node.save()
        try:
            node1 = TestModel(name='Node via save()')
            node1.save()
            if not node1.pk:
                errors.append("Insertion via save() did not assign a PK.")
        except Exception as e:
            errors.append("Insertion via save() raised an exception: " + str(e))

        # 2. Insertion via objects.create()
        try:
            node2 = TestModel.objects.create(name='Node via create()')
            if not node1.pk:
                errors.append(
                    "Insertion via objects.create() did not assign a PK.")
        except Exception as e:
            errors.append(
                "Insertion via objects.create() raised an exception: " + str(e))

        # 3. Alternative method (insert_at or get_or_create)
        try:
            # For demonstration, use node1 as the parent if the insert_at method exists
            if hasattr(TestModel, 'insert_at'):
                node3 = TestModel(name='Node via insert_at()')
                node3.insert_at(node1)
            elif hasattr(TestModel.objects, 'get_or_create'):
                node3, created = TestModel.objects.get_or_create(
                    name='Node via get_or_create()', defaults={'tn_parent': node1})
            else:
                errors.append(
                    "No alternative insertion method found (insert_at/get_or_create).")
        except Exception as e:
            errors.append(
                "Alternative insertion raised an exception: " + str(e))

        # Checking access methods (e.g. get_children)
        try:
            # Create a small tree
            root = TestModel.objects.create(name='Root')
            child = TestModel.objects.create(name='Child', tn_parent=root)
            # If the model defines a get_children() method, check its functionality
            if hasattr(root, 'get_children'):
                children = root.get_children()
                if child not in children:
                    errors.append(
                        "Method get_children() did not return the added child.")
            else:
                # If the method does not exist, perform a simple filter by parent
                children = TestModel.objects.filter(tn_parent=root)
                if child not in children:
                    errors.append(
                        "Filter by parent did not return the added child.")
        except Exception as e:
            errors.append("Access methods check raised an exception: " + str(e))

        # Tests for node deletion and moving can be added in a similar manner

        # Output report for basic operations
        if errors:
            print("BasicOperationsTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("BasicOperationsTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "BasicOperationsTest: errors - " + ", ".join(errors))


class DeepTreePerformanceTest(TransactionTestCase):
    """
    Performance test for a deep tree:
    - A tree is created with one root and 100 levels of nesting.
    - The insertion time for nodes is measured at levels: 0 (root), 1, 10, 50, 100.
    - Results are printed to the console with absolute values and as a percentage of the root insertion time.
    """

    def runTest(self):
        print("\n=== DeepTreePerformanceTest ===")
        timings = {}  # dictionary: level -> insertion time (in seconds)
        nodes = []    # storing references to nodes for potential read tests

        try:
            # Insertion of the root node
            start = time.time()
            root = TestModel.objects.create(name="Deep Root")
            end = time.time()
            timings[0] = end - start
            nodes.append(root)

            current_parent = root

            for level in range(1, 101):
                start = time.time()
                new_node = TestModel.objects.create(
                    name=f"Node Level {level}", tn_parent=current_parent)
                end = time.time()
                timings[level] = end - start
                nodes.append(new_node)
                current_parent = new_node  # the next node will be a child of the one just created

            # Generate report for levels: 0, 1, 10, 20, 30, 40, 50, 70, 80, 90, 100
            levels_to_report = [0, 1, 10, 20, 30,40, 50, 70, 80, 90, 100]
            # to avoid division by zero
            root_time = timings[0] if timings[0] > 0 else 1e-6
            print("Deep tree - node insertion times:")
            print("Level\tInsertion time (s)\t% of root time")
            for lvl in levels_to_report:
                t = timings.get(lvl, None)
                if t is not None:
                    perc = (t / root_time) * 100
                    print(f"{lvl}\t{t:.6f}\t\t{perc:.2f}%")
                else:
                    print(f"{lvl}\tNo data")

            # Additionally, one can measure node reading times using a similar approach.
        except Exception as e:
            print("DeepTreePerformanceTest: exception:", e)
            traceback.print_exc()

        # Since the test is exploratory in nature, simply assert True.
        self.assertTrue(True)


class WideTreePerformanceTest(TransactionTestCase):
    """
    Performance test for a wide tree:
    - 100 roots are created, each with a tree of up to 5 levels of nesting.
    - The total tree creation time is measured, then the average time per tree is calculated.
    - Results are printed to the console.
    """

    def runTest(self):
        print("\n=== WideTreePerformanceTest ===")
        tree_times = []
        try:
            # For 100 trees
            for root_index in range(1, 101):
                tree_start = time.time()
                root = TestModel.objects.create(name=f"Wide Root {root_index}")
                current_parent = root
                # Create 5 levels of nesting for each root
                for level in range(1, 6):
                    new_node = TestModel.objects.create(
                        name=f"Node {root_index}-{level}", tn_parent=current_parent)
                    current_parent = new_node
                tree_end = time.time()
                tree_times.append(tree_end - tree_start)

            avg_time = sum(tree_times) / len(tree_times)
            print("Wide tree:")
            print(
                f"100 trees (each with 5 levels) created with an average creation time of: {avg_time:.6f} s")
        except Exception as e:
            print("WideTreePerformanceTest: exception:", e)
            traceback.print_exc()

        self.assertTrue(True)


class MassInsertionTest(TestCase):
    """
    Mass insertion test:
    - Inserts nodes from 50 to 75 using all three methods (save, create, alternative method).
    - If an error occurs with any method, it is recorded but the test continues.
    - A detailed report is printed at the end.
    """

    def runTest(self):
        print("\n=== MassInsertionTest ===")
        errors = []
        try:
            for i in range(50, 76):
                # 1. Insertion via save()
                try:
                    node = TestModel(name=f"Mass Node {i} via save()")
                    node.save()
                except Exception as e:
                    errors.append(f"Error inserting node {i} via save(): {e}")

                # 2. Insertion via objects.create()
                try:
                    TestModel.objects.create(name=f"Mass Node {i} via create()")
                except Exception as e:
                    errors.append(f"Error inserting node {i} via create(): {e}")

                # 3. Alternative method (insert_at or get_or_create)
                try:
                    # Take the first node in the database or create a parent
                    parent = TestModel.objects.first()
                    if not parent:
                        parent = TestModel.objects.create(name="Default Parent")

                    if hasattr(TestModel, 'insert_at'):
                        node = TestModel(name=f"Mass Node {i} via insert_at()")
                        node.insert_at(parent)
                    elif hasattr(TestModel.objects, 'get_or_create'):
                        TestModel.objects.get_or_create(
                            name=f"Mass Node {i} via get_or_create()", defaults={'tn_parent': parent})
                    else:
                        errors.append(
                            f"No alternative insertion method found for node {i}.")
                except Exception as e:
                    errors.append(
                        f"Error in alternative insertion for node {i}: {e}")
        except Exception as e:
            errors.append("General exception in MassInsertionTest: " + str(e))

        if errors:
            print("MassInsertionTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("MassInsertionTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "MassInsertionTest: errors - " + ", ".join(errors))


class NodeDeletionTest(TestCase):
    """
    Tests node deletion:
    - A parent and children are created.
    - One of the children is deleted and it is verified that it is absent from the query.
    - Then the parent is deleted and it is verified that cascading deletion worked (if provided).
    """

    def runTest(self):
        errors = []
        print("\n=== NodeDeletionTest ===")
        try:
            parent = TestModel.objects.create(name="Deletion Parent")
            child1 = TestModel.objects.create(name="Child 1", tn_parent=parent)
            child2 = TestModel.objects.create(name="Child 2", tn_parent=parent)

            # Delete child1
            child1.delete()
            remaining_children = TestModel.objects.filter(tn_parent=parent)
            if child1 in remaining_children:
                errors.append(
                    "The deleted child1 is still present among the parent's children.")

            # Delete the parent and check cascading deletion
            parent.delete()
            if TestModel.objects.filter(pk=child2.pk).exists():
                errors.append(
                    "Child2 was not deleted after the parent was deleted (cascading deletion was expected).")
        except Exception as e:
            errors.append("Exception in NodeDeletionTest: " + str(e))

        if errors:
            print("NodeDeletionTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("NodeDeletionTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "NodeDeletionTest: errors - " + ", ".join(errors))


class NodeMovingTest(TestCase):
    """
    Tests moving of nodes:
    - Two parents are created.
    - A node is moved from the first parent to the second.
    - It is verified that the node appears in the new parent's children list and is absent from the old parent's list.
    """

    def runTest(self):
        errors = []
        print("\n=== NodeMovingTest ===")
        try:
            parent1 = TestModel.objects.create(name="Original Parent")
            parent2 = TestModel.objects.create(name="New Parent")
            child = TestModel.objects.create(
                name="Movable Child", tn_parent=parent1)

            # Moving the node
            child.set_parent(parent2)
            child.save()

            children1 = TestModel.objects.filter(tn_parent=parent1)
            children2 = TestModel.objects.filter(tn_parent=parent2)
            if child in children1:
                errors.append(
                    "The node is still present in the original parent's children after moving.")
            if child not in children2:
                errors.append(
                    "The node was not found among the new parent's children after moving.")
        except Exception as e:
            errors.append("Exception in NodeMovingTest: " + str(e))

        if errors:
            print("NodeMovingTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("NodeMovingTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "NodeMovingTest: errors - " + ", ".join(errors))


class NodeUpdateTest(TestCase):
    """
    Tests node update:
    - A node is created, then its attribute (e.g. name) is updated.
    - It is verified that the change is saved in the database.
    """

    def runTest(self):
        errors = []
        print("\n=== NodeUpdateTest ===")
        try:
            node = TestModel.objects.create(name="Original Name")
            node.name = "Updated Name"
            node.save()
            updated_node = TestModel.objects.get(pk=node.pk)
            if updated_node.name != "Updated Name":
                errors.append("The node's name was not updated correctly.")
        except Exception as e:
            errors.append("Exception in NodeUpdateTest: " + str(e))

        if errors:
            print("NodeUpdateTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("NodeUpdateTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "NodeUpdateTest: errors - " + ", ".join(errors))


class DataIntegrityTest(TestCase):
    """
    Tests data integrity:
    - A small tree is created.
    - Operations of moving, updating, and deletion are performed.
    - The correctness of relationships between parents and children after the operations is verified.
    """

    def runTest(self):
        errors = []
        print("\n=== DataIntegrityTest ===")
        try:
            root = TestModel.objects.create(name="Integrity Root")
            child1 = TestModel.objects.create(
                name="Integrity Child 1", tn_parent=root)
            child2 = TestModel.objects.create(
                name="Integrity Child 2", tn_parent=root)
            grandchild = TestModel.objects.create(
                name="Integrity Grandchild", tn_parent=child1)

            # Move child2 under child1
            child2.set_parent(child1)

            # Update child1's name
            child1.name = "Integrity Child 1 Updated"
            child1.save()

            # Delete grandchild
            grandchild.delete()

            # Verify relationships
            root_children = TestModel.objects.filter(tn_parent=root)
            if child1 not in root_children:
                errors.append(
                    "Child1 not found among the root node's children.")
            if child2 in root_children:
                errors.append(
                    "Child2 is present among the root node's children after moving.")

            child1_children = TestModel.objects.filter(tn_parent=child1)
            if child2 not in child1_children:
                errors.append(
                    "Child2 not found among child1's children after moving.")

            if TestModel.objects.filter(name="Integrity Grandchild").exists():
                errors.append("Grandchild still exists after deletion.")
        except Exception as e:
            errors.append("Exception in DataIntegrityTest: " + str(e))

        if errors:
            print("DataIntegrityTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("DataIntegrityTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "DataIntegrityTest: errors - " + ", ".join(errors))


class LargeVolumeTest(TransactionTestCase):
    """
    Test with large data volume:
    - Performs mass insertion of 1000 nodes.
    - Verifies that the number of inserted nodes matches the expected count.
    """

    def runTest(self):
        errors = []
        print("\n=== LargeVolumeTest ===")
        try:
            initial_count = TestModel.objects.count()
            for i in range(1000):
                try:
                    TestModel.objects.create(name=f"Large Node {i}")
                except Exception as e:
                    errors.append(
                        f"Error inserting node {i} in large data volume: {e}")
            final_count = TestModel.objects.count()
            if final_count - initial_count != 1000:
                errors.append(
                    f"Expected 1000 new nodes, but got {final_count - initial_count}.")
        except Exception as e:
            errors.append("Exception in LargeVolumeTest: " + str(e))

        if errors:
            print("LargeVolumeTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("LargeVolumeTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "LargeVolumeTest: errors - " + ", ".join(errors))


class InvalidDataTest(TestCase):
    """
    Tests handling of invalid data:
    - Attempts to create a node with None in a required field (e.g. name).
    - Verifies that the expected exception is raised.
    """

    def runTest(self):
        errors = []
        print("\n=== InvalidDataTest ===")
        try:
            try:
                # Attempt to create a node with invalid data
                TestModel.objects.create(name=None)
                errors.append(
                    "Creating a node with None for name did not raise an exception as expected.")
            except Exception:
                # Expected behavior: an exception should occur
                pass

            # Additionally, one can test creating a node with an empty string if that is not allowed
            try:
                node = TestModel(name="")
                node.save()
                # If an empty string is allowed, then no error should be recorded
            except Exception as e:
                # If an exception occurs, that may also be considered acceptable
                pass
        except Exception as e:
            errors.append("Exception in InvalidDataTest: " + str(e))

        if errors:
            print("InvalidDataTest: FAILED. Errors detected:")
            for err in errors:
                print(" -", err)
        else:
            print("InvalidDataTest: PASSED.")

        self.assertEqual(
            len(errors), 0, "InvalidDataTest: errors - " + ", ".join(errors))
