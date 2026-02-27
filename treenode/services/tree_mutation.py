# -*- coding: utf-8 -*-
"""
Tree mutation service.

Version: 3.0.7
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.db import transaction


class TreeMutationService:
    """Service class for transactional tree mutations."""

    def __init__(self, model):
        """Initialize service with model class."""
        self.model = model

    def move_node(self, node, target, position):
        """Move a node transactionally and run tree update tasks immediately."""
        with transaction.atomic():
            parent_ids = self._get_affected_parent_ids(
                node=node,
                target=target,
                position=position,
            )
            for parent_id in parent_ids:
                list(
                    self.model.objects.filter(parent_id=parent_id)
                    .select_for_update(nowait=True)
                    .values_list("pk", flat=True)
                )

            node.move_to(target, position)
            self.model.tasks.run()

    def _get_affected_parent_ids(self, node, target, position):
        old_parent_id = node.parent_id
        new_parent_id = self._resolve_new_parent_id(target=target, position=position)

        parent_ids = [old_parent_id]
        if new_parent_id != old_parent_id:
            parent_ids.append(new_parent_id)
        return parent_ids

    def _resolve_new_parent_id(self, target, position):
        if target is None:
            return None

        sibling_positions = {
            "first-sibling",
            "left-sibling",
            "right-sibling",
            "last-sibling",
            "sorted-sibling",
        }
        if position in sibling_positions:
            return target.parent_id
        return target.pk


# The End
