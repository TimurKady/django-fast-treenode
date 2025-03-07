# -*- coding: utf-8 -*-
"""
Closure Table Manager and QuerySet

This module defines custom managers and query sets for the ClosureModel.
It includes optimized bulk operations for handling hierarchical data
using the Closure Table approach.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from collections import deque, defaultdict
from django.db import models, transaction


# ----------------------------------------------------------------------------
# Closere Model
# ----------------------------------------------------------------------------


class ClosureQuerySet(models.QuerySet):
    """QuerySet для ClosureModel."""

    def sort_nodes(self, node_list):
        """
        Sort nodes topologically.

        Returns a list of nodes sorted from roots to leaves.
        A node is considered a root if its tn_parent is None or its
        parent is not in node_list.
        """
        visited = set()  # Will store the ids of already processed nodes
        result = []
        # Set of node ids included in the original list
        node_ids = {node.id for node in node_list}

        def dfs(node):
            if node.id in visited:
                return
            # If there is a parent and it is included in node_list, then
            # process it first
            if node.tn_parent and node.tn_parent_id in node_ids:
                dfs(node.tn_parent)
            visited.add(node.id)
            result.append(node)

        for n in node_list:
            dfs(n)

        return result

    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000, *args, **kwargs):
        """Insert new nodes in bulk."""
        result = []

        # 1. Topological sorting of nodes
        objs = self.sort_nodes(objs)

        # 1. Create self-links for all nodes: (node, node, 0, node).
        self_links = [
            self.model(parent=obj, child=obj, depth=0, node=obj)
            for obj in objs
        ]
        result.extend(
            super(ClosureQuerySet, self).bulk_create(
                self_links, batch_size, *args, **kwargs
            )
        )

        # 2. We form a display: parent id -> list of its children.
        children_map = defaultdict(list)
        for obj in objs:
            if obj.tn_parent_id:
                children_map[obj.tn_parent_id].append(obj)

        # 3. We try to determine the root nodes (with tn_parent == None).
        root_nodes = [obj for obj in objs if obj.tn_parent is None]

        # If there are no root nodes, then we insert a subtree.
        if not root_nodes:
            # Define the "top" nodes of the subtree:
            # those whose parent is not included in the list of inserted objects
            objs_ids = {obj.id for obj in objs if obj.id is not None}
            top_nodes = [
                obj for obj in objs if obj.tn_parent_id not in objs_ids
            ]

            # For each such node, if the parent exists, get the closure records
            # for the parent and add new records for (ancestor -> node) with
            # depth = ancestor.depth + 1.
            new_entries = []
            for node in top_nodes:
                if node.tn_parent_id:
                    parent_closures = self.model.objects.filter(
                        child_id=node.tn_parent_id
                    )
                    for ancestor in parent_closures:
                        new_entries.append(
                            self.model(
                                parent=ancestor.parent,
                                child=node,
                                depth=ancestor.depth + 1
                            )
                        )
            if new_entries:
                result.extend(
                    super(ClosureQuerySet, self).bulk_create(
                        new_entries, batch_size, *args, **kwargs
                    )

                )

            # Set the top-level nodes of the subtree as the starting ones for
            # traversal.
            current_nodes = top_nodes
        else:
            current_nodes = root_nodes

        def process_level(current_nodes):
            """Recursive function for traversing levels."""
            next_level = []
            new_entries = []
            for node in current_nodes:
                # For the current node, we get all the closure records
                # (its ancestors).
                ancestors = self.model.objects.filter(child=node)
                for child in children_map.get(node.id, []):
                    for ancestor in ancestors:
                        new_entries.append(
                            self.model(
                                parent=ancestor.parent,
                                child=child,
                                depth=ancestor.depth + 1
                            )
                        )
                    next_level.append(child)
            if new_entries:
                result.extend(
                    super(ClosureQuerySet, self).bulk_create(
                        new_entries, batch_size, *args, **kwargs
                    )
                )
            if next_level:
                process_level(next_level)

        # 4. Run traversing levels.
        process_level(current_nodes)
        return result

    @transaction.atomic
    def bulk_update(self, objs, fields=None, batch_size=1000):
        """
        Update the closure table for objects whose tn_parent has changed.

        It is assumed that all objects from the objs list are already in the
        closure table, but their links (both for parents and for children) may
        have changed.

        Algorithm:
        1. Form a mapping: parent id → list of its children.
        2. Determine the root nodes of the subtree to be updated:
        – A node is considered a root if its tn_parent is None or its
        parent is not in objs.
        3. For each root node, if there is an external parent, get its
        closure from the database.
        Then form closure records for the node (all external links with
        increased depth and self-reference).
        4. Using BFS, traverse the subtree: for each node, for each of its
        children, create records using parent records (increased by 1) and add
        a self-reference for the child.
        5. Remove old closure records for objects from objs and save new ones in
        batches.
        """
        # 1. Topological sorting of nodes
        objs = self.sort_nodes(objs)

        # 2. Let's build a mapping: parent id → list of children
        children_map = defaultdict(list)
        for obj in objs:
            if obj.tn_parent_id:
                children_map[obj.tn_parent_id].append(obj)

        # Set of id's of objects to be updated
        objs_ids = {obj.id for obj in objs}

        # 3. Determine the root nodes of the updated subtree:
        # A node is considered root if its tn_parent is either None or its
        # parent is not in objs.
        roots = [
            obj for obj in objs
            if (obj.tn_parent is None) or (obj.tn_parent_id not in objs_ids)
        ]

        # List for accumulating new closure records
        new_closure_entries = []

        # Queue for BFS: each element is a tuple (node, node_closure), where
        # node_closure is a list of closure entries for that node.
        queue = deque()
        for node in roots:
            if node.tn_parent_id:
                # Get the closure of the external parent from the database
                external_ancestors = list(
                    self.model.objects.filter(child_id=node.tn_parent_id)
                    .values('parent_id', 'depth')
                )
                # For each ancestor found, create an entry for node with
                # depth+1
                node_closure = [
                    self.model(
                        parent_id=entry['parent_id'],
                        child=node,
                        depth=entry['depth'] + 1
                    )
                    for entry in external_ancestors
                ]
            else:
                node_closure = []
            # Add self-reference (node ​​→ node, depth 0)
            node_closure.append(
                self.model(parent=node, child=node, depth=0, node=node)
            )

            # Save records for the current node and put them in a queue for
            # processing its subtree
            new_closure_entries.extend(node_closure)
            queue.append((node, node_closure))

        # 4. BFS subtree traversal: for each node, create a closure for its
        # children
        while queue:
            parent_node, parent_closure = queue.popleft()
            for child in children_map.get(parent_node.id, []):
                # For the child, new closure records:
                # for each parent record, create (ancestor -> child) with
                # depth+1
                child_closure = [
                    self.model(
                        parent_id=entry.parent_id,
                        child=child,
                        depth=entry.depth + 1
                    )
                    for entry in parent_closure
                ]
                # Add a self-link for the child
                child_closure.append(
                    self.model(parent=child, child=child, depth=0)
                )

                new_closure_entries.extend(child_closure)
                queue.append((child, child_closure))

        # 5. Remove old closure records for updatable objects
        self.model.objects.filter(child_id__in=objs_ids).delete()

        # 6. Save new records in batches
        super(ClosureQuerySet, self).bulk_create(new_closure_entries)


class ClosureModelManager(models.Manager):
    """ClosureModel Manager."""

    def get_queryset(self):
        """get_queryset method."""
        return ClosureQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=1000):
        """Create objects in bulk."""
        return self.get_queryset().bulk_create(objs, batch_size=batch_size)

    def bulk_update(self, objs, fields=None, batch_size=1000):
        """Move nodes in ClosureModel."""
        return self.get_queryset().bulk_update(
            objs, fields, batch_size=batch_size
        )
