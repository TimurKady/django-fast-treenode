# -*- coding: utf-8 -*-
"""
Managers and QuerySets

This module defines custom managers and query sets for the TreeNode model.
It includes optimized bulk operations for handling hierarchical data
using the Closure Table approach.

Features:
- `ClosureQuerySet` and `ClosureModelManager` for managing closure records.
- `TreeNodeQuerySet` and `TreeNodeModelManager` for adjacency model operations.
- Optimized `bulk_create` and `bulk_update` methods with atomic transactions.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import models, transaction


# ----------------------------------------------------------------------------
# Closere Model
# ----------------------------------------------------------------------------


class ClosureQuerySet(models.QuerySet):
    """QuerySet для ClosureModel."""

    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000):
        """
        Insert new nodes in bulk.

        For newly created AdjacencyModel objects:
        1. Create self-referential records (parent=child, depth=0).
        2. Build ancestors for each node based on tn_parent.
        """
        # --- 1. Create self-referential closure records for each object.
        self_closure_records = []
        for item in objs:
            self_closure_records.append(
                self.model(parent=item, child=item, depth=0)
            )
        super().bulk_create(self_closure_records, batch_size=batch_size)

        # --- 2. Preparing closure for parents
        parent_ids = {node.tn_parent.pk for node in objs if node.tn_parent}
        parent_closures = list(
            self.filter(child__in=parent_ids)
                .values('child', 'parent', 'depth')
        )
        # Pack them into a dict
        parent_closures_dict = {}
        for pc in parent_closures:
            parent_id = pc['child']
            parent_closures_dict.setdefault(parent_id, []).append(pc)

        # --- 3. Get closure records for the objs themselves
        node_ids = [node.pk for node in objs]
        child_closures = list(
            self.filter(parent__in=node_ids)
                .values('parent', 'child', 'depth')
        )
        child_closures_dict = {}
        for cc in child_closures:
            parent_id = cc['parent']
            child_closures_dict.setdefault(parent_id, []).append(cc)

        # --- 4. Collecting new links
        new_records = []
        for node in objs:
            if not node.tn_parent:
                continue
            # parent closure
            parents = parent_closures_dict.get(node.tn_parent.pk, [])
            # closure of descendants
            # (often this is only the node itself, depth=0, but there can be
            # nested ones)
            children = child_closures_dict.get(node.pk, [])
            # Combine parents x children
            for p in parents:
                for c in children:
                    new_records.append(self.model(
                        parent_id=p['parent'],
                        child_id=c['child'],
                        depth=p['depth'] + c['depth'] + 1
                    ))
        # --- 5. bulk_create
        result = []
        if new_records:
            result = super().bulk_create(new_records, batch_size=batch_size)
        self.model.clear_cache()
        return result

    @transaction.atomic
    def bulk_update(self, objs, fields=None, batch_size=1000):
        """
        Update the records in the closure table for the list of updated nodes.

        For each node whose tn_parent has changed, the closure records
        for its entire subtree are recalculated:
        1. The ancestor chain of the new parent is selected.
        2. The subtree (with closure records) of the updated node is selected.
        3. For each combination (ancestor, descendant), a new depth is
           calculated.
        4. Old "dangling" records (those where the descendant has a link to
           a non-subtree) are removed.
        5. New records are inserted using the bulk_create method.
        """
        if not objs:
            return

        # --- 1. We obtain chains of ancestors for new parents.
        parent_ids = {node.tn_parent.pk for node in objs if node.tn_parent}
        parent_closures = list(
            self.filter(child__in=parent_ids).values(
                'child',
                'parent',
                'depth'
            )
        )
        # We collect in a dictionary: key is the parent ID (tn_parent),
        # value is the list of records.
        parent_closures_dict = {}
        for pc in parent_closures:
            parent_closures_dict.setdefault(pc['child'], []).append(pc)

        # --- 2. Obtain closing records for the subtrees of the
        # nodes being updated.
        updated_ids = [node.pk for node in objs]
        subtree_closures = list(self.filter(parent__in=updated_ids).values(
            'parent',
            'child',
            'depth'
        ))
        # Group by ID of the node being updated (i.e. by parent in the
        # closing record)
        subtree_closures_dict = {}
        for sc in subtree_closures:
            subtree_closures_dict.setdefault(sc['parent'], []).append(sc)

        # --- 3. Construct new close records for each updated node with
        # a new parent.
        new_records = []
        for node in objs:
            # If the node has become root (tn_parent=None), then there are
            # no additional connections with ancestors.
            if not node.tn_parent:
                continue
            # From the closing chain of the new parent we get a list of its
            # ancestors
            p_closures = parent_closures_dict.get(node.tn_parent.pk, [])
            # From the node subtree we get the closing records
            s_closures = subtree_closures_dict.get(node.pk, [])
            # If for some reason the subtree entries are missing, we will
            # ensure that there is a custom entry.
            if not s_closures:
                s_closures = [{
                    'parent': node.pk,
                    'child': node.pk,
                    'depth': 0
                }]
            # Combine: for each ancestor of the new parent and for each
            # descendant from the subtree
            for p in p_closures:
                for s in s_closures:
                    new_depth = p['depth'] + s['depth'] + 1
                    new_records.append(
                        self.model(
                            parent_id=p['parent'],
                            child_id=s['child'],
                            depth=new_depth
                        )
                    )

        # --- 4. Remove old closing records so that there are no "tails".
        # For each updated node, calculate a subset of IDs related to its
        # subtree
        for node in objs:
            subtree_ids = set()
            # Be sure to include the node itself (its self-link should
            # already be there)
            subtree_ids.add(node.pk)
            for sc in subtree_closures_dict.get(node.pk, []):
                subtree_ids.add(sc['child'])
            # Remove records where the child belongs to the subtree, but the
            # parent is not included in it.
            self.filter(child_id__in=subtree_ids).exclude(
                parent_id__in=subtree_ids).delete()

        # --- 5. Insert new closing records in bulk.
        if new_records:
            super().bulk_create(new_records, batch_size=batch_size)
        self.model.clear_cache()
        return new_records


class ClosureModelManager(models.Manager):
    """ClosureModel Manager."""

    def get_queryset(self):
        """get_queryset method."""
        return ClosureQuerySet(self.model, using=self._db)

    def bulk_create(self, objs, batch_size=1000):
        """Create objects in bulk."""
        self.model.clear_cache()
        return self.get_queryset().bulk_create(objs, batch_size=batch_size)

    def bulk_update(self, objs, fields=None, batch_size=1000):
        """Move nodes in ClosureModel."""
        self.model.clear_cache()
        return self.get_queryset().bulk_update(
            objs, fields, batch_size=batch_size
        )

# ----------------------------------------------------------------------------
# TreeNode Model
# ----------------------------------------------------------------------------


class TreeNodeQuerySet(models.QuerySet):
    """TreeNodeModel QuerySet."""

    def __init__(self, model=None, query=None, using=None, hints=None):
        """Init."""
        self.closure_model = model.closure_model
        super().__init__(model, query, using, hints)

    @transaction.atomic
    def bulk_create(self, objs, batch_size=1000, ignore_conflicts=False):
        """
        Bulk create.

        Method of bulk creation objects with updating and processing of
        the Closuse Model.
        """
        # Regular bulk_create for TreeNodeModel
        objs = super().bulk_create(objs, batch_size, ignore_conflicts)
        # Call ClosureModel to insert closure records
        self.closure_model.objects.bulk_create(objs, batch_size=batch_size)
        # Возвращаем результат
        self.model.clear_cache()
        return self.filter(pk__in=[obj.pk for obj in objs])

    @transaction.atomic
    def bulk_update(self, objs, fields, batch_size=1000, **kwargs):
        """."""
        closure_model = self.model.closure_model
        if 'tn_parent' in fields:
            # Попросим ClosureModel обработать move
            closure_model.objects.bulk_update(objs)
        result = super().bulk_update(objs, fields, batch_size, **kwargs)
        closure_model.clear_cache()
        return result


class TreeNodeModelManager(models.Manager):
    """TreeNodeModel Manager."""

    def bulk_create(self, objs, batch_size=1000, ignore_conflicts=False):
        """
        Bulk Create.

        Override bulk_create for the adjacency model.
        Here we first clear the cache, then delegate the creation via our
        custom QuerySet.
        """
        self.model.clear_cache()
        return self.get_queryset().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )

    def get_queryset(self):
        """Return a QuerySet that sorts by 'tn_parent' and 'tn_priority'."""
        queryset = TreeNodeQuerySet(self.model, using=self._db)
        return queryset.order_by('tn_parent', 'tn_priority')

# The End
