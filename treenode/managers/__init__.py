# -*- coding: utf-8 -*-
"""
Managers and QuerySets

This module defines custom managers and query sets for the TreeNode model.
It includes optimized bulk operations for handling hierarchical data
using the Closure Table approach.

Features:
- `ClosureModelManager` for managing closure records.
- `TreeNodeModelManager` for adjacency model operations.

Version: 2.1.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from .closure import ClosureModelManager
from .adjacency import TreeNodeModelManager

__all__ = ["TreeNodeModelManager", "ClosureModelManager"]
