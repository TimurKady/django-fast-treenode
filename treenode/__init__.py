default_app_config = 'treenode.apps.TreeNodeConfig'

from .middleware import TreeNodeFlushMiddleware

__all__ = ['TreeNodeFlushMiddleware']
