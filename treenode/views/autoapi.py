# -*- coding: utf-8 -*-
"""
Route generator for all models inherited from TreeNodeModel

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.apps import apps
from django.urls import path
from django.conf import settings
from django.contrib.auth.decorators import login_required

from ..models import TreeNodeModel
from .autocomplete import TreeNodeAutocompleteView
from .children import TreeChildrenView
from .search import TreeSearchView
from .crud import TreeNodeBaseAPIView


class AutoTreeAPI:
    """Auto-discover and expose TreeNode-based APIs."""

    def __init__(self, base_view=TreeNodeBaseAPIView, base_url="api"):
        """Init auto-discover."""
        self.base_view = base_view
        self.base_url = base_url

    def protect_view(self, view, model):
        """
        Protect view.

        Protects view with login_required if needed, based on model attribute
        or global settings.
        """
        if getattr(model, 'api_login_required', None) is True:
            return login_required(view)
        if getattr(settings, 'TREENODE_API_LOGIN_REQUIRED', False):
            return login_required(view)
        return view

    def discover(self):
        """Scan models and generate API urls."""
        urls = [
            # Admin and Widget end-points
            path("widget/autocomplete/", TreeNodeAutocompleteView.as_view(), name="tree_autocomplete"),  # noqa: D501
            path("widget/children/", TreeChildrenView.as_view(), name="tree_children"),  # noqa: D501
            path("widget/search/", TreeSearchView.as_view(), name="tree_search"),  # noqa: D501
        ]
        for model in apps.get_models():
            if issubclass(model, TreeNodeModel) and model is not TreeNodeModel:
                model_name = model._meta.model_name

                # Dynamically create an API view class for the model
                api_view_class = type(
                    f"{model_name.capitalize()}APIView",
                    (self.base_view,),
                    {"model": model}
                )

                # List of API actions and their corresponding URL patterns
                action_patterns = [
                    # List / Create
                    ("", None, f"{model_name}-list"),
                    # Retrieve / Update / Delete
                    ("<int:pk>/", None, f"{model_name}-detail"),
                    ("tree/", {'action': 'tree'}, f"{model_name}-tree"),
                    # Direct children
                    ("<int:pk>/children/", {'action': 'children'}, f"{model_name}-children"),  # noqa: D501
                    # All descendants
                    ("<int:pk>/descendants/", {'action': 'descendants'}, f"{model_name}-descendants"),   # noqa: D501
                    # Ancestors + Self + Descendants
                    ("<int:pk>/family/", {'action': 'family'}, f"{model_name}-family"),   # noqa: D501
                ]

                # Create secured view instance once
                view = self.protect_view(api_view_class.as_view(), model)

                # Automatically build all paths for this model
                for url_suffix, extra_kwargs, route_name in action_patterns:
                    urls.append(
                        path(
                            f"{self.base_url}/{model_name}/{url_suffix}",
                            view,
                            extra_kwargs or {},
                            name=route_name
                        )
                    )
        return urls
