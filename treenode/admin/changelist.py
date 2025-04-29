# -*- coding: utf-8 -*-
"""
TreeNode Sorted ChangeList Class for TreeNodeModelAdmin.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.contrib.admin.views.main import ChangeList
from django.forms.models import modelformset_factory
from django.db.models import Q


class TreeNodeChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_ordering(self, request, queryset):
        """
        Override ordering.

        Overrides the sort order of objects in the list.
        Django Admin sorts by `-pk` (descending) by default.
        This method removes `-pk` so that objects are not sorted by ID.
        """
        # Remove the default '-pk' ordering if present.
        ordering = list(super().get_ordering(request, queryset))
        if '-pk' in ordering:
            ordering.remove('-pk')
        return tuple(ordering)

    def get_results(self, request):
        super().get_results(request)
        model_name = self.model._meta.model_name

        # Добавляем атрибуты к результатам
        object_ids = [r.pk for r in self.result_list]
        objects_dict = {
            obj.pk: obj
            for obj in self.model_admin.model.objects.filter(pk__in=object_ids)
        }

        for result in self.result_list:
            result.obj = objects_dict.get(result.pk)
            # Добавляем атрибуты строк
            result.row_attrs = f'data-node-id="{result.pk}" data-parent-of="{result.obj.parent_id or ""}" class="model-{model_name} pk-{result.pk}"'
