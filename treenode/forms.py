"""
TreeNode Form Module.

This module defines the TreeNodeForm class, which dynamically determines
the TreeNode model.
It utilizes TreeWidget and automatically excludes the current node and its
descendants from the parent choices.

Functions:
- __init__: Initializes the form and filters out invalid parent choices.
- factory: Dynamically creates a form class for a given TreeNode model.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.forms import ModelForm
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from django.utils.translation import gettext_lazy as _

from .widgets import TreeWidget


class SortedModelChoiceIterator(ModelChoiceIterator):
    """Iterator Class for ModelChoiceField."""

    def __iter__(self):
        """Return sorted choices based on tn_order."""
        qs_list = list(self.queryset.order_by('_path').all())

        # Iterate yield (value, label) pairs.
        for obj in qs_list:
            yield (
                self.field.prepare_value(obj),
                self.field.label_from_instance(obj)
            )


class SortedModelChoiceField(ModelChoiceField):
    """ModelChoiceField Class for tn_paret field."""

    to_field_name = None

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        choices = list(SortedModelChoiceIterator(self))
        if self.empty_label is not None:
            choices.insert(0, ("", self.empty_label))
        return choices

    def _set_choices(self, value):
        self._choices = value

    choices = property(_get_choices, _set_choices)


class TreeNodeForm(ModelForm):
    """TreeNodeModelAdmin Form Class."""

    def __init__(self, *args, **kwargs):
        """Init Form."""
        super(TreeNodeForm, self).__init__(*args, **kwargs)
        self.model = self.instance._meta.model

        if 'parent' not in self.fields:
            return

        exclude_pks = []
        if self.instance.pk:
            exclude_pks = self.instance.query(
                objects='descendants',
                include_self=True
            )

        queryset = self.model.objects\
            .exclude(pk__in=exclude_pks)\
            .order_by('_path')\
            .all()

        self.fields['parent'].queryset = queryset
        self.fields["parent"].required = False
        self.fields["parent"].empty_label = _("Root")

        original_field = self.fields["parent"]

        self.fields["parent"] = SortedModelChoiceField(
            queryset=queryset,
            label=original_field.label,
            widget=original_field.widget,
            empty_label=original_field.empty_label,
            required=False
        )
        self.fields["parent"].widget.model = self.model

        # If there is a current value, set it
        if self.instance and self.instance.pk and self.instance.parent:
            self.fields["parent"].initial = self.instance.parent

    class Meta:
        widgets = {
            'parent': TreeWidget(),
        }

# The End
