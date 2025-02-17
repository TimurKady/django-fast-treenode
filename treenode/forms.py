"""
TreeNode Form Module.

This module defines the TreeNodeForm class, which dynamically determines the TreeNode model.
It utilizes TreeWidget and automatically excludes the current node and its descendants
from the parent choices.

Functions:
- __init__: Initializes the form and filters out invalid parent choices.
- factory: Dynamically creates a form class for a given TreeNode model.

Version: 2.0.10
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django import forms
import numpy as np
from django.forms.models import ModelChoiceField, ModelChoiceIterator

from .widgets import TreeWidget


class SortedModelChoiceIterator(ModelChoiceIterator):
    """Iterator Class for ModelChoiceField."""

    def __iter__(self):
        """Return sorted choices based on tn_order."""
        qs_list = list(self.queryset.all())
        # Sort objects by their tn_order using NumPy.
        tn_orders = np.array([obj.tn_order for obj in qs_list])
        sorted_indices = np.argsort(tn_orders)
        # Iterate over sorted indices and yield (value, label) pairs.
        for idx in sorted_indices:
            # Cast the index to int if it is numpy.int64.
            obj = qs_list[int(idx)]
            yield (
                self.field.prepare_value(obj),
                self.field.label_from_instance(obj)
            )


class SortedModelChoiceField(ModelChoiceField):
    """ModelChoiceField Class for tn_paret field."""

    def _get_choices(self):
        """Get sorted choices."""
        if hasattr(self, '_choices'):
            return self._choices
        return SortedModelChoiceIterator(self)

    def _set_choices(self, value):
        """Set choices."""
        self._choices = value

    choices = property(_get_choices, _set_choices)


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

        # Use a model bound to a form
        model = self._meta.model

        if "tn_parent" in self.fields and self.instance.pk:
            excluded_ids = [self.instance.pk] + \
                list(self.instance.get_descendants_pks())
            queryset = model.objects.exclude(pk__in=excluded_ids)
            original_field = self.fields["tn_parent"]
            self.fields["tn_parent"] = SortedModelChoiceField(
                queryset=queryset,
                label=self.fields["tn_parent"].label,
                widget=original_field.widget
            )

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
