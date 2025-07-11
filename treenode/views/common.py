# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 19:50:23 2025

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.apps import apps
from django.http import Http404

from ..models import TreeNodeModel

def get_model_from_request(request):
    """Get model from request."""
    model_label = request.GET.get("model")
    if not model_label:
        raise Http404("Missing 'model' parameter.")
    try:
        app_label, model_name = model_label.lower().split(".")
        model = apps.get_model(app_label, model_name)
    except Exception:
        raise Http404(f"Invalid model format: {model_label}")

    # Ensure the model is a subclass of TreeNodeModel
    if not issubclass(model, TreeNodeModel):
        raise Http404(f"{model_label} is not a TreeNodeModel.")

    return model
