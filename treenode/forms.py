"""
TreeNode Form Module.

This module defines the TreeNodeForm class, which dynamically determines the TreeNode model.
It utilizes TreeWidget and automatically excludes the current node and its descendants
from the parent choices.

Functions:
- __init__: Initializes the form and filters out invalid parent choices.
- factory: Dynamically creates a form class for a given TreeNode model.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django import forms
from .widgets import TreeWidget
from django.db.models import Case, When, Value, IntegerField


class TreeNodeForm(forms.ModelForm):
    """
    TreeNode Form Class.

    ModelForm for dynamically determined TreeNode model.
    Uses TreeWidget and excludes self and descendants from the parent choices.
    """

    class Meta:
        """Meta Class."""

        model = None
        fields = "__all__"
        widgets = {
            "tn_parent": TreeWidget()
        }

    def __init__(self, *args, **kwargs):
        """Init Method."""
        super().__init__(*args, **kwargs)

        # Get the model from the form instance
        # Use a model bound to a form
        model = self._meta.model

        # Проверяем наличие tn_parent и исключаем текущий узел и его потомков
        if "tn_parent" in self.fields and self.instance.pk:
            excluded_ids = [self.instance.pk] + list(
                self.instance.get_descendants_pks())

            # Sort by tn_order
            queryset = model.objects.exclude(pk__in=excluded_ids)
            node_list = sorted(queryset, key=lambda x: x.tn_order)
            pk_list = [node.pk for node in node_list]
            queryset = queryset.filter(pk__in=pk_list).order_by(
                Case(*[When(pk=pk, then=Value(index))
                       for index, pk in enumerate(pk_list)],
                     default=Value(len(pk_list)),
                     output_field=IntegerField())
            )

            # Set QuerySet
            self.fields["tn_parent"].queryset = queryset

    @classmethod
    def factory(cls, model):
        """
        Create a form class dynamically for the given TreeNode model.

        This ensures that the form works with different concrete models.
        """
        class Meta:
            model = model
            fields = "__all__"
            widgets = {
                "tn_parent": TreeWidget(
                    attrs={
                        "data-autocomplete-light": "true",
                        "data-url": "/tree-autocomplete/",
                    }
                )
            }

        return type(f"{model.__name__}Form", (cls,), {"Meta": Meta})


# The End
