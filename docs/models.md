## Model Inheritance and Extensions

### Model Inheritance

Creating your own tree model is very easy. Simply inherit from `TreeNodeModel`. Below is an example of a basic category model:

**models.py**

```python
from django.db import models
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):
    treenode_display_field = "name"  # Defines the field used for display in the admin panel

    name = models.CharField(max_length=50)

    class Meta(TreeNodeModel.Meta):  # Preserve TreeNodeModel's indexing settings
        verbose_name = "Category"
        verbose_name_plural = "Categories"
```

!!! important
    Always specify `TreeNodeModel.Meta` as the parent of your model’s `Meta` class. Failing to do so will result in incorrect database indexing and other negative consequences.

---

### Class and Instance Attributes

This section describes the class and instance attributes available when interacting with a tree model. Understanding these attributes will help you avoid subtle bugs and write cleaner, more efficient code.

#### `node.parent`
The core field of any tree node model is the `parent` field. It is a `ForeignKey` that establishes a many-to-one relationship between nodes, forming the tree hierarchy.

!!! tip
    Although the `parent` field is always up-to-date and can be accessed directly, it is good practice to use the `get_parent()` and `set_parent()` methods for better consistency.

#### `cls.treenode_display_field`
Defines the field used to display nodes in the Django admin panel. If not set, nodes are shown generically as `"Node <id>"`.

#### `cls.sorting_field`
Specifies the field used to sort sibling nodes. Defaults to `"priority"`, but can be customized.

!!! warning
    The `priority` field exists on each model instance. Although it is accessible, you should **never** read or set its value directly.

    Due to internal caching mechanisms, the visible value might not match the actual database value. Using `refresh_from_db()` is expensive and clears model caches. Instead, always use the `get_priority()` and `set_priority()` methods.

If you specify another field, for example `name`, the tree will be sorted by that field alphabetically:

```python
class Category(TreeNodeModel):
    sorting_field = "name"
    ...
```

#### `cls.sorting_direction`
An optional attribute that controls the default sorting order (ascending or descending) for siblings.

It must be set to a value from the [**SortingChoices**](#sortingchoices-class) class.

Other internal attributes should not be modified directly. Use the provided public methods instead.


### `cls.api_login_required`
Each model in the tree can define the `api_login_required` class attribute. The `True` value enables [API access control for each model](apifirst.md#) via Django's login system (`login_required`). In this case, all API endpoints for the model will require the user to be logged in.

```python
class Category(TreeNodeModel):
    api_login_required = False
    ...
```

!!! warning
    If `api_login_required` attribute is not explicitly defined, the API for the model **remains open** by default.
    In production environments, **API endpoints must not remain open**.

---

### Built-in Classes

#### SortingChoices Class

`SortingChoices` is a built-in helper class defined inside `TreeNodeModel`. It provides clear constants for sorting direction:

| Value | Meaning |
|:------|:--------|
| `SortingChoices.ASC` | Sort ascending (lowest to highest priority). Default. |
| `SortingChoices.DESC` | Sort descending (highest to lowest priority). |

You can reference it inside your model:

```python
class Category(TreeNodeModel):
    sorting_direction = SortingChoices.DESC
```

Since `SortingChoices` is attached to the model class, no separate import is required.

---

#### Meta Class

When extending `TreeNodeModel`, always inherit from `TreeNodeModel.Meta` to preserve essential database indexing.

To add your own indexes:

```python
class Category(TreeNodeModel):
    treenode_display_field = "name"
    name = models.CharField(max_length=50)

    class Meta(TreeNodeModel.Meta):
        verbose_name = "Category"
        verbose_name_plural = "Categories"

        indexes = list(TreeNodeModel._meta.indexes) + [
            models.Index(fields=["name"]),
        ]
```

This approach ensures full Django integration, efficient queries, and correct hierarchical behavior.

---

### Model Extending

Extending `TreeNodeModel` is flexible and straightforward. You can freely add custom fields and methods.

Example:

```python
class Category(TreeNodeModel):
    treenode_display_field = "name"
    sorting_field = "name"
    sorting_direction = SortingChoices.DESC

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=5)

    class Meta(TreeNodeModel.Meta):
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def get_full_string(self):
        return f"{self.code} - {self.name}"
```

The framework places no restrictions on functionality expansion.

---

### Model Manager

When creating a custom model manager, always extend `TreeNodeModelManager` instead of modifying internal components like `TreeNodeQuerySet`.

Example of a safe custom manager:

```python
from treenode.managers import TreeNodeModelManager

class CustomTreeNodeManager(TreeNodeModelManager):
    def active(self):
        """Return only active nodes."""
        return self.get_queryset().filter(is_active=True)
```

Or if you want to override `get_queryset()` itself:

```python
class CustomTreeNodeManager(TreeNodeModelManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
```

Following these principles ensures your managers remain **safe**, **future-proof**, and **compatible** with the tree structure.
