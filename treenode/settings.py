# -*- coding: utf-8 -*-
"""
TreeNodeModel and TreeCache settings.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from django.conf import settings


CACHE_LIMIT = getattr(settings, "TREENODE_CACHE_LIMIT", 100) * 1024 * 1024

# The length on Materialized Path segment
SEGMENT_LENGTH = getattr(settings, "TREENODE_SEGMENT_LENGTH", 3)

# Serialization dictionary: hexadecimal encoding, fixed segment size
SEGMENT_BASE = 16

# Nubber children per one tree node
BASE = SEGMENT_BASE ** SEGMENT_LENGTH  # 4096


TREENODE_PAD_CHAR = getattr(settings, "TREENODE_PAD_CHAR", "'0'")


# The End
