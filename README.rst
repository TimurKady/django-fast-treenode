================================================================================

FAST TREENODE

Application for supporting tree (hierarchical) data structure in Django projects
Combination of Adjacency List and Closure Table

================================================================================


Quick start
-----------

Add "fast-treeneode" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "fast-treeneode",
        ...
    ]

When updating an existing project, simply call cls.update_tree() function once. 
It will automatically build a new and complete Closure Table for your tree.

