# -*- coding: utf-8 -*-
"""

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.http import JsonResponse
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .common import get_model_from_request


@method_decorator(staff_member_required, name='dispatch')
class TreeChildrenView(View):
    def get(self, request, *args, **kwargs):
        model = get_model_from_request(request)
        reference_id = request.GET.get("reference_id")
        if not reference_id:
            return JsonResponse({"results": []})

        obj = model.objects.filter(pk=reference_id).first()
        if not obj or obj.is_leaf():
            return JsonResponse({"results": []})

        results = [
            {
                "id": node.pk,
                "text": str(node),
                "level": node.get_depth(),
                "is_leaf": node.is_leaf(),
            }
            for node in obj.get_children()
        ]
        return JsonResponse({"results": results})


# The End
