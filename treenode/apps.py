"""
TreeNode configuration definition module.

Customization:
- checks the correctness of the sorting fields
- checks the correctness of model inheritance
- starts asynchronous loading of node data into the cache

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.apps import apps, AppConfig


class TreeNodeConfig(AppConfig):
    """Config Class."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "treenode"

    def ready(self):
        """Ready method."""
        from .models import TreeNodeModel

        # Models checking
        subclasses = [
            m for m in apps.get_models()
            if issubclass(m, TreeNodeModel) and m is not TreeNodeModel
        ]

        for model in subclasses:

            field_names = {f.name for f in model._meta.get_fields()}

            # Check display_field is correct
            if model.display_field is not None:
                if model.display_field not in field_names:
                    raise ValueError(
                        f'Invalid display_field "{model.display_field}. "'
                        f'Available fields: {field_names}')

            # Check sorting_field is correct
            if model.sorting_field is not None:
                if model.sorting_field not in field_names:
                    raise ValueError(
                        f'Invalid sorting_field "{model.sorting_field}. "'
                        f'Available fields: {field_names}')

            # Check if Meta is a descendant of TreeNodeModel.Meta
            if not issubclass(model.Meta, TreeNodeModel.Meta):
                raise ValueError(
                    f'{model.__name__} must inherit Meta class ' +
                    'from TreeNodeModel.Meta.'
                )
