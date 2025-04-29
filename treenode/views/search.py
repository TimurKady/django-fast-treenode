# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 19:53:56 2025

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.apps import apps
from django.db.models import Q


@method_decorator(staff_member_required, name="dispatch")
class TreeSearchView(View):
    """Search view for TreeNode models used in admin interface."""

    def get(self, request, *args, **kwargs):
        app_label = request.GET.get("app")
        model_name = request.GET.get("model")
        query = request.GET.get("q", "").strip()

        if not (app_label and model_name and query):
            return JsonResponse({"results": []})

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return JsonResponse({"results": []})

        # Получаем queryset и ищем по __str__, через Q с contains
        queryset = model.objects.all()
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(pk__icontains=query))[:20]

        results = [
            {
                "id": obj.pk,
                "text": str(obj),
                "is_leaf": obj.is_leaf(),
            }
            for obj in queryset
        ]
        return JsonResponse({"results": results})
