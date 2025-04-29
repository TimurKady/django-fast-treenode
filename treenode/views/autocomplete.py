# -*- coding: utf-8 -*-
"""


Handles autocomplete suggestions for TreeNode models.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

# autocomplete.py
from django.http import JsonResponse
from django.views import View
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .common import get_model_from_request


@method_decorator(staff_member_required, name='dispatch')
class TreeNodeAutocompleteView(View):
    """Widget Autocomplete View."""

    def get(self, request, *args, **kwargs):
        """Get request."""
        select_id = request.GET.get("select_id", "").strip()
        q = request.GET.get("q", "").strip()

        model = get_model_from_request(request)
        results = []

        if q:
            field = getattr(model, "display_field", "id")
            queryset = model.objects.filter(**{f"{field}__icontains": q})
        elif select_id:
            pk = int(select_id)
            queryset = model.objects.filter(pk=pk)
        else:
            queryset = model.objects.filter(parent__isnull=True)

        results = [
            {
                "id": obj.pk,
                "text": str(obj),
                "level": obj.get_depth(),
                "is_leaf": obj.is_leaf(),
            }
            for obj in queryset[:20]
        ]

        return JsonResponse({"results": results})
