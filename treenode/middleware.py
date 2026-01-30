# -*- coding: utf-8 -*-
"""
TreeNode Middleware Module

This module provides Django middleware for flushing the tree task queue
at the end of each request, preventing nested transaction issues that
occur when tasks.run() is called during queryset iteration.

Version: 3.2.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import logging
from django.apps import apps


class TreeNodeFlushMiddleware:
    """
    Middleware that flushes all TreeNode task queues at the end of each request.

    This prevents nested transaction errors that occur when tasks.run()
    is called automatically during queryset iteration (e.g., during drag-and-drop
    operations in the admin panel).

    Usage:
        Add to MIDDLEWARE in settings.py:
        MIDDLEWARE = [
            ...
            'treenode.middleware.TreeNodeFlushMiddleware',
        ]
    """

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request and flush task queues after response."""
        response = self.get_response(request)

        # Flush all TreeNode task queues after request completes
        self._flush_all_queues()

        return response

    def _flush_all_queues(self):
        """Flush task queues for all TreeNodeModel subclasses."""
        # Import here to avoid circular imports
        from .models import TreeNodeModel

        for model in apps.get_models():
            if issubclass(model, TreeNodeModel) and model is not TreeNodeModel:
                if hasattr(model, 'tasks'):
                    tasks = model.tasks
                    if hasattr(tasks, 'queue') and len(tasks.queue) > 0:
                        try:
                            tasks.run()
                        except Exception as e:
                            logging.error(
                                "TreeNodeFlushMiddleware: Error flushing queue "
                                "for %s: %s",
                                model.__name__, e
                            )


# The End
