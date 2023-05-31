# -*- coding: utf-8 -*-
"""
TreeNode Managers Module

"""

from django.db import models


class TreeNodeQuerySet(models.QuerySet):
    """TreeNode Manager QuerySet Class"""

    def __init__(self, model=None, query=None, using=None, hints=None):
        self.closure_model = model.closure_model
        super().__init__(model, query, using, hints)

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        objs = super().bulk_create(objs, batch_size, ignore_conflicts)

        objs = self.model.closure_model.bulk_create([
            self.model.closure_model(
                parent=item,
                child=item,
                depth=0
            )
        ] for item in objs)

        for node in objs:
            qs = self.model.closure_model.objects.all()
            parents = qs.filter(child=node.tn_parent).values('parent', 'depth')
            children = qs.filter(parent=node).values('child', 'depth')
            objects = [
                self.model.closure_model(
                    parent_id=p['parent'],
                    child_id=c['child'],
                    depth=p['depth'] + c['depth'] + 1
                )
                for p in parents
                for c in children
            ]
            node._closure_model.objects.bulk_create(objects)

        self.model._update_orders()
        return objs


class TreeNodeManager(models.Manager):
    """TreeNode Manager Class"""

    def get_queryset(self):
        return TreeNodeQuerySet(self.model, using=self._db)


# End
