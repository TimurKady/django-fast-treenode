# -*- coding: utf-8 -*-
"""
API-First Support Module.

CRUD and Tree Operations for TreeNode models.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import json
import logging
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.http import (
    JsonResponse, HttpResponseBadRequest, HttpResponseNotFound,
)
from django.utils.translation import gettext_lazy as _
from django.views import View

logger = logging.getLogger("treenode.views.crud")


class TreeNodeBaseAPIView(View):
    """Simple API View for TreeNode-based models."""

    model = None

    def get_queryset(self):
        """Return base queryset."""
        return self.model.objects.get_queryset()

    def dispatch(self, request, *args, **kwargs):
        """Ddispatch request."""
        self.action = kwargs.pop('action', None)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk=None):
        """
        Handle GET requests depending on action.

        Get a list of all nodes:
        GET	/treenode/api/<model>/?flat=true

        Get one node:
        GET	/treenode/api/<model>/<id>/

        Get the whole tree:
        GET	/treenode/api/<model>/tree/

        Get the annotated tree:
        GET	/treenode/api/<model>/tree/?annotated=true

        Only node own children:
        GET	/treenode/api/<model>/<id>/children/

        All descendants:
        GET	/treenode/api/<model>/<id>/descendants/

        Get a family:
        GET	/treenode/api/<model>/<id>/family/
        """
        # Action mode
        if self.action == "tree":
            annotated = request.GET.get("annotated", "false").lower() == "true"
            if annotated:
                data = self.model.get_tree_annotated()
            else:
                data = self.model.get_tree()
            return JsonResponse(data, safe=False)

        if self.action == "children" and pk:
            try:
                node = self.get_queryset().get(pk=pk)
                children = node.get_children()
                data = [model_to_dict(obj) for obj in children]
                return JsonResponse(data, safe=False)
            except self.model.DoesNotExist:
                return HttpResponseNotFound("Node not found.")

        if self.action == "descendants" and pk:
            try:
                node = self.get_queryset().get(pk=pk)
                descendants = node.get_descendants()
                data = [model_to_dict(obj) for obj in descendants]
                return JsonResponse(data, safe=False)
            except self.model.DoesNotExist:
                return HttpResponseNotFound("Node not found.")

        if self.action == "family" and pk:
            try:
                node = self.get_queryset().get(pk=pk)
                family = node.get_family()
                data = [model_to_dict(obj) for obj in family]
                return JsonResponse(data, safe=False)
            except self.model.DoesNotExist:
                return HttpResponseNotFound("Node not found.")

        # Standard mode (if there is no special action)
        if pk is None:
            nodes = self.get_queryset().order_by("_path")
            data = [model_to_dict(obj) for obj in nodes]
            return JsonResponse(data, safe=False)
        else:
            try:
                obj = self.get_queryset().get(pk=pk)
                return JsonResponse(model_to_dict(obj))
            except self.model.DoesNotExist:
                return HttpResponseNotFound("Node not found.")

    def post(self, request):
        """
        Create a new node.

        POST /treenode/api/<model>/

        Body (JSON):
            {
                "name": "Node Name",
                "parent_id": 123,    # optional
                "priority": 0
            }

        Returns:
            - Created node as JSON
        """
        try:
            body = json.loads(request.body)
            obj = self.model(**body)
            obj.full_clean()
            obj.save()
            return JsonResponse(model_to_dict(obj), status=201)
        except ValidationError as ve:
            # give the client clear field errors
            return JsonResponse({"errors": ve.message_dict}, status=400)
        except Exception:
            # log full information for development
            logger.exception("Failed to create node")
            return JsonResponse(
                {"error": _("Failed to create node")}, status=400)

    def put(self, request, pk):
        """
        Replace a node.

        PUT /treenode/api/<model>/<id>/

        Body (JSON):
            {
                "name": "New Name",
                "parent_id": 124,
                "priority": 1
            }

        Returns:
            - Updated node as JSON
        """
        try:
            obj = self.get_queryset().get(pk=pk)
            body = json.loads(request.body)
            for field, value in body.items():
                setattr(obj, field, value)
            obj.full_clean()
            obj.save()
            return JsonResponse(model_to_dict(obj))
        except ValidationError as ve:
            return JsonResponse({"errors": ve.message_dict}, status=400)
        except self.model.DoesNotExist:
            # give the client clear field errors
            return HttpResponseNotFound(_("Node not found (pk={pk})."))
        except Exception:
            # log full information for development
            logger.exception("Error replacing node %s", pk)
            return JsonResponse(
                {"error": _("Failed to update node")}, status=400)

    def patch(self, request, pk):
        """
        Update a node (partially).

        PATCH /treenode/api/<model>/<id>/

        Body (JSON):
            {
                "priority": 2
            }

        Returns:
            - Updated node as JSON
        """
        return self.put(request, pk)

    def delete(self, request, pk):
        """
        Delete a node.

        DELETE /treenode/api/<model>/<id>/
            ?cascade=true    # default, delete node and descendants
            ?cascade=false   # move children up before deleting

        Returns:
            {
                "status": "deleted",
                "id": <deleted id>,
                "cascade": true|false
            }
        """
        try:
            cascade = not request.GET.get("cascade") == "false"
            obj = self.get_queryset().get(pk=pk)
            obj.delete(cascade=cascade)
            return JsonResponse({
                "status": "deleted",
                "id": obj.pk,
                "cascade": cascade
            })
        except ValidationError as ve:
            # give the client clear field errors|
            return JsonResponse({"errors": ve.message_dict}, status=400)
        except self.model.DoesNotExist:
            return HttpResponseNotFound(_("Node not found (pk={pk})."))
        except Exception:
            # log full information for development
            logger.exception("Error deleting node %s", pk)
            return JsonResponse(
                {"error": _("Error deleting node")}, status=400)


# The End
