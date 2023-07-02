# Django-fast-treenode 
__Combination of Adjacency List and Closure Table__

## Functions
Application for supporting tree (hierarchical) data structure in Django projects
* fast: the fastest of the two methods is used to process requests, combining the advantages of an **Adjacency Table** and a **Closure Table**,
* even faster: the main resource-intensive operations are **cached**; **bulk operations** are used for inserts and changes,
* synchronized: model instances in memory are automatically updated,
* compatibility: you can easily add a tree node to existing projects using TreeNode without changing the code,
* no dependencies,
* easy setup: just extend the abstract model/model-admin,
* admin integration: visualization options (accordion, breadcrumbs or padding),
* widget: Built-in Select2-to-Tree extends Select2 to support arbitrary nesting levels.

## Debut idea
This is a modification of the reusable [django-treenode](https://github.com/fabiocaccamo/django-treenode) application developed by [Fabio Caccamo](https://github.com/fabiocaccamo).
The original application has significant advantages over other analogues, and indeed, is one of the best implementations of support for hierarchical structures for Django. 

Fabio's idea was to use the Adjacency List method to store the data tree. The most probable and time-consuming requests are calculated in advance and stored in the database. Also, most requests are cached. As a result, query processing is carried out in one call to the database or without it at all.

However, this application has a number of undeniable shortcomings:
* the selected pre-calculations scheme entails high costs for adding a new element;
* inserting new elements uses signals, which leads to failures when using bulk-operations;
* the problem of ordering elements by priority inside the parent node has not been resolved.

My idea was to solve these problems by combining the adjacency list with the Closure Table. Main advantages:
* the Closure Model is generated automatically;
* maintained compatibility with the original package at the level of documented functions;
* most requests are satisfied in one call to the database;
* inserting a new element takes two calls to the database without signals usage;
* bulk-operations are supported;
* the cost of creating a new dependency is reduced many times;
* useful functionality added for some methods (e.g.  the `include_self=False` and `depth` parameters has been added to functions that return lists/querysets);
* additionally, the package includes a tree view widget for the `tn_parent` field in the change form.

Of course, at large levels of nesting, the use of the Closure Table leads to an increase in resource costs. But at the same time, the combined scheme still generally outperforms the original application in terms of performance.

## Theory
You can get a basic understanding of what is a Closure Table from:
* [presentation](https://www.slideshare.net/billkarwin/models-for-hierarchical-data) by Bill Karwin;
* [article](https://dirtsimple.org/2010/11/simplest-way-to-do-tree-based-queries.html) by blogger Dirt Simple;
* [article](https://towardsdatascience.com/closure-table-pattern-to-model-hierarchies-in-nosql-c1be6a87e05b) by Andriy Zabavskyy.

You can easily find additional information on your own on the Internet.

## Quick start
1. Run ```pip install django-fast-treenode```
2. Add ```treenode``` to ```settings.INSTALLED_APPS```
3. Make your model inherit from ```treenode.models.TreeNodeModel``` (described below)
4. Make your model-admin inherit from ```treenode.admin.TreeNodeModelAdmin``` (described below)
5. Run python manage.py makemigrations and ```python manage.py migrate```

When updating an existing project, simply call ```cls.update_tree()``` function once. 
It will automatically build a new and complete Closure Table for your tree.

## Configuration
### `models.py`
Make your model class inherit from `treenode.models.TreeNodeModel`:

```python
from django.db import models
from treenode.models import TreeNodeModel


class Category(TreeNodeModel):

    # the field used to display the model instance
    # default value 'pk'
    treenode_display_field = "name"

    name = models.CharField(max_length=50)

    class Meta(TreeNodeModel.Meta):
        verbose_name = "Category"
        verbose_name_plural = "Categories"
```

The `TreeNodeModel` abstract class adds many fields (prefixed with `tn_` to prevent direct access) and public methods to your models.

### `admin.py`
Make your model-admin class inherit from `treenode.admin.TreeNodeModelAdmin`.

```python
from django.contrib import admin

from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

from .models import Category


class CategoryAdmin(TreeNodeModelAdmin):

    # set the changelist display mode: 'accordion', 'breadcrumbs' or 'indentation' (default)
    # when changelist results are filtered by a querystring,
    # 'breadcrumbs' mode will be used (to preserve data display integrity)
    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION

    # use TreeNodeForm to automatically exclude invalid parent choices
    form = TreeNodeForm

admin.site.register(Category, CategoryAdmin)
```

---

### `settings.py`
You can use a custom cache backend by adding a `treenode` entry to `settings.CACHES`, otherwise the default cache backend will be used.

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "...",
    },
    "treenode": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}
```
### `forms.py`

```
class YoursForm(TreeNodeForm):

    class Meta:
        widgets = {
            'tn_parent': TreeWidget(attrs={'style': 'min-width:400px'}),
        }
```

## Usage

### Methods/Properties

-   [`delete`](#delete)
-   [`delete_tree`](#delete_tree)
-   [`get_ancestors`](#get_ancestors)
-   [`get_ancestors_count`](#get_ancestors_count)
-   [`get_ancestors_pks`](#get_ancestors_pks)
-   [`get_ancestors_queryset`](#get_ancestors_queryset)
-   [`get_breadcrumbs`](#get_breadcrumbs)
-   [`get_children`](#get_children)
-   [`get_children_count`](#get_children_count)
-   [`get_children_pks`](#get_children_pks)
-   [`get_children_queryset`](#get_children_queryset)
-   [`get_depth`](#get_depth)
-   [`get_descendants`](#get_descendants)
-   [`get_descendants_count`](#get_descendants_count)
-   [`get_descendants_pks`](#get_descendants_pks)
-   [`get_descendants_queryset`](#get_descendants_queryset)
-   [`get_descendants_tree`](#get_descendants_tree)
-   [`get_descendants_tree_display`](#get_descendants_tree_display)
-   [`get_first_child`](#get_first_child)
-   [`get_index`](#get_index)
-   [`get_last_child`](#get_last_child)
-   [`get_level`](#get_level)
-   [`get_order`](#get_order)
-   [`get_parent`](#get_parent)
-   [`get_parent_pk`](#get_parent_pk)
-   [`set_parent`](#set_parent)
-   [`get_path`](#get_path)
-   [`get_priority`](#get_priority)
-   [`set_priority`](#set_priority)
-   [`get_root`](#get_root)
-   [`get_root_pk`](#get_root_pk)
-   [`get_roots`](#get_roots)
-   [`get_roots_queryset`](#get_roots_queryset)
-   [`get_siblings`](#get_siblings)
-   [`get_siblings_count`](#get_siblings_count)
-   [`get_siblings_pks`](#get_siblings_pks)
-   [`get_siblings_queryset`](#get_siblings_queryset)
-   [`get_tree`](#get_tree)
-   [`get_tree_display`](#get_tree_display)
-   [`is_ancestor_of`](#is_ancestor_of)
-   [`is_child_of`](#is_child_of)
-   [`is_descendant_of`](#is_descendant_of)
-   [`is_first_child`](#is_first_child)
-   [`is_last_child`](#is_last_child)
-   [`is_leaf`](#is_leaf)
-   [`is_parent_of`](#is_parent_of)
-   [`is_root`](#is_root)
-   [`is_root_of`](#is_root_of)
-   [`is_sibling_of`](#is_sibling_of)
-   [`update_tree`](#update_tree)

#### `delete`
**Delete a node** if `cascade=True` (default behaviour), children and descendants will be deleted too,
otherwise children's parent will be set to `None` (then children become roots):
```python
obj.delete(cascade=True)
```

#### `delete_tree`
**Delete the whole tree** for the current node class:
```python
cls.delete_tree()
```

#### `get_ancestors`
Get a **list with all ancestors** (ordered from root to parent):
```python
obj.get_ancestors(include_self=True, depth=None)
# or
obj.ancestors
```

#### `get_ancestors_count`
Get the **ancestors count**:
```python
obj.get_ancestors_count(include_self=True, depth=None)
# or
obj.ancestors_count
```

#### `get_ancestors_pks`
Get the **ancestors pks** list:
```python
obj.get_ancestors_pks(include_self=True, depth=None)
# or
obj.ancestors_pks
```

#### `get_ancestors_queryset`
Get the **ancestors queryset** (ordered from parent to root):
```python
obj.get_ancestors_queryset(include_self=True, depth=None)
```

#### `get_breadcrumbs`
Get the **breadcrumbs** to current node (included):
```python
obj.get_breadcrumbs(attr=None)
# or
obj.breadcrumbs
```

#### `get_children`
Get a **list containing all children**:
```python
obj.get_children()
# or
obj.children
```

#### `get_children_count`
Get the **children count**:
```python
obj.get_children_count()
# or
obj.children_count
```

#### `get_children_pks`
Get the **children pks** list:
```python
obj.get_children_pks()
# or
obj.children_pks
```

#### `get_children_queryset`
Get the **children queryset**:
```python
obj.get_children_queryset()
```

#### `get_depth`
Get the **node depth** (how many levels of descendants):
```python
obj.get_depth()
# or
obj.depth
```

#### `get_descendants`
Get a **list containing all descendants**:
```python
obj.get_descendants(include_self=False, depth=None)
# or
obj.descendants
```

#### `get_descendants_count`
Get the **descendants count**:
```python
obj.get_descendants_count(include_self=False, depth=None)
# or
obj.descendants_count
```

#### `get_descendants_pks`
Get the **descendants pks** list:
```python
obj.get_descendants_pks(include_self=False, depth=None)
# or
obj.descendants_pks
```

#### `get_descendants_queryset`
Get the **descendants queryset**:
```python
obj.get_descendants_queryset(include_self=False, depth=None)
```

#### `get_descendants_tree`
Get a **n-dimensional** `dict` representing the **model tree**:
```python
obj.get_descendants_tree()
# or
obj.descendants_tree
```

#### `get_descendants_tree_display`
Get a **multiline** `string` representing the **model tree**:
```python
obj.get_descendants_tree_display(include_self=False, depth=None)
# or
obj.descendants_tree_display
```

#### `get_first_child`
Get the **first child node**:
```python
obj.get_first_child()
# or
obj.first_child
```

#### `get_index`
Get the **node index** (index in node.parent.children list):
```python
obj.get_index()
# or
obj.index
```

#### `get_last_child`
Get the **last child node**:
```python
obj.get_last_child()
# or
obj.last_child
```

#### `get_level`
Get the **node level** (starting from 1):
```python
obj.get_level()
# or
obj.level
```

#### `get_order`
Get the **order value** used for ordering:
```python
obj.get_order()
# or
obj.order
```

#### `get_parent`
Get the **parent node**:
```python
obj.get_parent()
# or
obj.parent
```

#### `get_parent_pk`
Get the **parent node pk**:
```python
obj.get_parent_pk()
# or
obj.parent_pk
```

#### `set_parent`
Set the **parent node**:
```python
obj.set_parent(parent_obj)
```

#### `get_priority`
Get the **node priority**:
```python
obj.get_priority()
# or
obj.priority
```
#### `get_path`
Added the function of decorating a **materialized path**. The path is formed according to the value of the `tn_priority` field.
```python
cls.get_path(prefix='', suffix='', delimiter='.', format_str='')
```

#### `set_priority`
Set the **node priority**:
```python
obj.set_priority(100)
```

#### `get_root`
Get the **root node** for the current node:
```python
obj.get_root()
# or
obj.root
```

#### `get_root_pk`
Get the **root node pk** for the current node:
```python
obj.get_root_pk()
# or
obj.root_pk
```

#### `get_roots`
Get a **list with all root nodes**:
```python
cls.get_roots()
# or
cls.roots
```

#### `get_roots_queryset`
Get **root nodes queryset**:
```python
cls.get_roots_queryset()
```

#### `get_siblings`
Get a **list with all the siblings**:
```python
obj.get_siblings()
# or
obj.siblings
```

#### `get_siblings_count`
Get the **siblings count**:
```python
obj.get_siblings_count()
# or
obj.siblings_count
```

#### `get_siblings_pks`
Get the **siblings pks** list:
```python
obj.get_siblings_pks()
# or
obj.siblings_pks
```

#### `get_siblings_queryset`
Get the **siblings queryset**:
```python
obj.get_siblings_queryset()
```

#### `get_tree`
Returns an **n-dimensional dictionary** representing the model tree. Each node 
contains a "children"=[] key with a list of nested dictionaries of child nodes.:
```python
cls.get_tree(instance=None)
# or
cls.tree
```

#### `get_tree_display`
Get a **multiline** `string` representing the **model tree**:
```python
cls.get_tree_display()
# or
cls.tree_display
```

#### `is_ancestor_of`
Return `True` if the current node **is ancestor** of target_obj:
```python
obj.is_ancestor_of(target_obj)
```

#### `is_child_of`
Return `True` if the current node **is child** of target_obj:
```python
obj.is_child_of(target_obj)
```

#### `is_descendant_of`
Return `True` if the current node **is descendant** of target_obj:
```python
obj.is_descendant_of(target_obj)
```

#### `is_first_child`
Return `True` if the current node is the **first child**:
```python
obj.is_first_child()
```

#### `is_last_child`
Return `True` if the current node is the **last child**:
```python
obj.is_last_child()
```

#### `is_leaf`
Return `True` if the current node is **leaf** (it has not children):
```python
obj.is_leaf()
```

#### `is_parent_of`
Return `True` if the current node **is parent** of target_obj:
```python
obj.is_parent_of(target_obj)
```

#### `is_root`
Return `True` if the current node **is root**:
```python
obj.is_root()
```

#### `is_root_of`
Return `True` if the current node **is root** of target_obj:
```python
obj.is_root_of(target_obj)
```

#### `is_sibling_of`
Return `True` if the current node **is sibling** of target_obj:
```python
obj.is_sibling_of(target_obj)
```

#### `update_tree`
**Update tree** manually, useful after **bulk updates**:
```python
cls.update_tree()
```

## License
Released under [MIT License](https://github.com/TimurKady/django-fast-treenode/blob/main/LICENSE).

## Cautions
The provided code is already being used in production projects, even though I have only done general testing. That is why the risk of using the code lies entirely with you.

**Warning**: don't access the tree node fields directly! Most of them have been removed as unnecessary. In the future, only `tn_parent` and `tn_priority` will be kept. Use the functions described in the documentation above or the documentation for the [original application](https://github.com/fabiocaccamo/django-treenode). 

## Credits
This software contains, uses, including in a modified form:
*  [django-treenode](https://github.com/fabiocaccamo/django-treenode) by [Fabio Caccamo](https://github.com/fabiocaccamo);
*  [Select2-to-Tree](https://github.com/clivezhg/select2-to-tree) Select2 extension by [clivezhg](https://github.com/clivezhg)

Special thanks to [Mathieu Leplatre](https://blog.mathieu-leplatre.info/pages/about.html) for the advice used in writing this application

## To do
Future plans:
* may be will add the ability to determine the priority of the parent by any field, for example, by creation date or alphabetical order;
* drug-and-drop support;
* to be happy, to don't worry, until die.


Your wishes, objections, comments are welcome.
