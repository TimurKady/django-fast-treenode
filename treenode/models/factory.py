# -*- coding: utf-8 -*-
"""
TreeNode Factory

This module provides a metaclass that automatically associates a model with
a service table and creates a set of indexes for the database

Features:
- Dynamically creates and assigns a service model.
- Facilitates the formation of indexes taking into account the DB vendor.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.db import models, connection
from django.db.models import Func, F


class TreeNodeModelBase(models.base.ModelBase):
    """Base Class for TreeNodeModel."""

    def __new__(mcls, name, bases, attrs, **kwargs):
        """Create a New Class."""
        new_class = super().__new__(mcls, name, bases, attrs, **kwargs)
        if not new_class._meta.abstract:
            class_name = name.lower()
            # Create an index with the desired name
            """Set DB Indexes with unique names per model."""
            vendor = connection.vendor
            indexes = []

            if vendor == 'postgresql':
                indexes.append(models.Index(
                    fields=['_path'],
                    name=f'idx_{class_name}_path_ops',
                    opclasses=['text_pattern_ops']
                ))
            elif vendor in {'mysql'}:
                indexes.append(models.Index(
                    Func(F('_path'), function='md5'),
                    name=f'idx_{class_name}_path_hash'
                ))
            else:
                indexes.append(models.Index(
                    fields=['_path'],
                    name=f'idx_{class_name}_path'
                ))

            # Update the list of indexes
            new_class._meta.indexes += indexes

        return new_class

# The End
