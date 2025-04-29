# -*- coding: utf-8 -*-
"""
TreeNode URLs Module.

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

from .views import AutoTreeAPI

app_name = "treenode"


urlpatterns = [
    *AutoTreeAPI().discover(),
]
