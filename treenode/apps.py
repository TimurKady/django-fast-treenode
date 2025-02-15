# -*- coding: utf-8 -*-
"""
TreeNode Application Configuration

This module defines the application configuration for the TreeNode app.
It sets the default auto field and specifies the app's name.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.apps import AppConfig


class TreeNodeConfig(AppConfig):
    """TreeNodeConfig Class."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "treenode"


