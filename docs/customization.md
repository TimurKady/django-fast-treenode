## Advanced: Customization Guide

This section provides detailed guidance for advanced users who want to extend or fine-tune TreeNode Framework behavior while preserving full compatibility and upgradeability.

---

### Overriding Tree Behavior

Sometimes you may need to customize how tree operations behave beyond the default logic provided by TreeNode Framework. This can include modifying how children are retrieved, how nodes are moved or deleted, or how trees are traversed. The framework is designed to make such customizations straightforward without breaking internal cache consistency or auto-generated APIs.

In some cases, default tree operations may not fully match your project’s requirements. TreeNode Framework is designed to be flexible: key behaviors such as retrieving children, moving nodes, or deleting subtrees can be overridden safely without breaking internal consistency or cache integrity.

Core operations like `get_children()`, `move_to()`, and `delete()` are implemented as methods on the TreeNodeModel base class. You can override these methods in your own model classes to implement custom logic — for example, to restrict movement rules, modify deletion behavior, or automatically log operations.

```python

class Category(TreeNodeModel):
    treenode_display_field = "name"

    def get_children(self):
        """Return only active children."""
        return super().get_children().filter(is_active=True)

    def move_to(self, new_parent, position='first-child'):
        """By default, place the node in the first position and log every move operation."""
        print(f"Moving {self.name} to new parent {new_parent.name if new_parent else 'Root'}")
        return super().move(new_parent)

```

In this example, `get_children()` is customized to exclude inactive nodes. The `move_to()` method is extended to add simple logging before executing the default move behavior. The method signature has also been changed.

Both overrides maintain the original cache updates and internal task handling automatically, because the base `super()` calls are preserved.

!!! hint
    When you override model methods, assume that they are already cached and it doesn't make sense to re-apply the `@cached_method` decorator to them.

!!! tip "Best Practices"

    - Always call the corresponding `super()` method to preserve core logic (e.g., cache updates, signals).
    - Keep overrides simple and predictable to avoid side effects.
    - If adding complex business rules, prefer validating before calling `super()`, rather than after.
    - Document custom behaviors clearly in your codebase, especially if they affect API outputs.

---

### Custom Sorting Strategies

TreeNode Framework supports flexible node ordering using the `sorting_field` setting, which defaults to `"priority"`.  

Internally, this sorting logic is deeply integrated at the SQL level and tightly coupled with path generation, cache consistency, and indexing for performance reasons.

!!! warning
    **Do not modify or bypass methods related to**:
    
    - `_path` or `_depth` updates,
    - the `update_path()` method,
    - sorting strategies implemented via low-level SQL expressions.
    
    This can lead to data corruption or cache instability.  
    Always use the **recommended mechanism** described below.

Instead of overriding the sorting mechanism itself, the correct approach is to update the `priority` values of nodes and trigger a background update of the tree structure.

**Recommended Workflow**:

1. Leave `sorting_field = "priority"` unchanged.
2. Write a function that assigns `priority` values using your own logic.
3. Use `bulk_update()` to apply the changes.
    ```python
    cls.objects.bulk_update(update, fields=['priority'])
    ```

When performing batch updates across multiple parent nodes, the task optimizer will automatically consolidate and minimize the number of actual tree rebuilds.

For example:

```python
@classmethod
def reorder_children_by_name(cls, parent):
    children = parent.get_children().order_by("name")
    update = []
    for i, node in enumerate(children):
        node.set_priority(i)
        update.append(node)
    cls.objects.bulk_update(update, fields=['priority'])

```

This function reorders all direct children of a given parent alphabetically by name.
It assigns incremental priority values and triggers a fast, cache-aware subtree update using the built-in task queue.

!!! tip "Best Practices"

    - Do not change the `sorting_field`. Always sort via priority.
    - Apply updates in bulk to reduce write overhead. Let the task optimizer eliminate redundant updates automatically.
    - Avoid assigning duplicate priority values unless you explicitly control their meaning.
    - Keep sorting logic inside reusable service functions, not inline in views or signals.

---

### Adding Custom API Actions

Treenode Framework automatically generates all standard REST API endpoints using `AutoTreeAPI` class. To add custom actions, you should extend your models' behavior (at the model level) or create lightweight utility views separately, without disrupting the auto-generated API structure.

For example, lets create easy extending the model:

**models.py**
```python

class Category(TreeNodeModel):

    def get_descendants_flat(self):
        return list(self.get_descendants_queryset())
```

You can then call it from the standard API view (using query parameters or frontend).

**views.py**
```python
from django.http import JsonResponse
from django.views import View
from .models import Category

class CategoryFlatDescendantsAPI(View):
    def get(self, request, pk):
        node = Category.objects.get(pk=pk)
        descendants = node.get_descendants()
        data = [{"id": n.id, "name": str(n)} for n in descendants]
        return JsonResponse(data, safe=False)
```
And add one extra URL manually without touching the AutoTreeAPI structure:

**urls.py**
```python
from treenode.views.autoapi import AutoTreeAPI

urlpatterns = [
    *AutoTreeAPI().discover(),  # This is important!
    path(
        'api/category/<int:pk>/descendants-flat/',
        CategoryFlatDescendantsAPI.as_view(),
        name='category-flat-descendants'
    ),
]
```

!!! tip "Best Practices"
    - Never override or manually replace the auto-generated API view.
    - Extend the model where possible (add new methods).
    - Add external lightweight views only for truly special cases.
    - Keep auto-generated and custom APIs separate and modular.

---

### Integration with Permissions and Security

TreeNode Framework is intentionally designed to remain lightweight and flexible.  Instead of embedding a built-in permission system, it integrates naturally with Django’s standard authentication and authorization mechanisms (`auth`, `contenttypes`, `permissions`). This approach ensures maximum flexibility while keeping the core tree management operations fast and portable.

!!! attention
    You are responsible for applying access controls at the model, view, and API levels.  

TreeNode Framework supports three main layers of security:

| Layer | Purpose | Recommended for |
|:------|:--------|:----------------|
| **Model-level permissions** | Enforce access based on `add`, `change`, and `delete` model permissions. | Simple CRUD access control. |
| **Object-level permissions** | Control access on a per-node basis (e.g., who can move or delete a specific node). | Complex ownership and delegation models. |
| **API endpoint protection** | Restrict API access using Django’s `login_required` or permission mixins. | Public-facing or admin APIs. |

!!! hint "Recommended Security Practices"

    - Always **check permissions** before executing business-critical operations like `move_to()`, `delete()`, and `update()`.
    - Use Django’s `PermissionRequiredMixin` or custom middleware to secure your API endpoints.
    - Apply object-level access control inside model methods when dealing with fine-grained permissions.
    - Raise `PermissionDenied` exceptions early if an operation is not authorized.
    - Keep permission logic separated from low-level tree maintenance code.

Look example of checking permissions in model operations:

```python
from django.core.exceptions import PermissionDenied

class Category(TreeNodeModel):
    treenode_display_field = "name"

    def move_to(self, target, position='last-child'):
        if not self.can_user_move(self.current_user):  # Your custom logic
            raise PermissionDenied("You are not allowed to move this node.")
        return super().move(target, position)

    def can_user_move(self, user):
        # Define your project-specific rules here
        return user.is_staff or self.owner == user
```

Another example illustrates enabling protection for an automatically generated API:

```python
from django.contrib.auth.mixins import PermissionRequiredMixin
from treenode.views.autoapi import AutoTreeAPI

class SecuredTreeAPI(PermissionRequiredMixin, AutoTreeAPI):
    permission_required = 'myapp.change_category'
    raise_exception = True
```

And in **urls.py**:

```python

urlpatterns = [
    *SecuredTreeAPI().discover(),
]
```

This method ensures that only users with the specified permission can access the entire tree API.

!!! tip "Best Practices"

    - Apply permission checks explicitly — TreeNode Framework will not enforce them automatically.
    - Prefer lightweight, focused permission logic tied to business operations, not to low-level data structures.
    - Clearly document permission rules in your project to avoid unexpected behavior in multi-user environments.
    - **Remember**: tree integrity and cache consistency are maintained automatically, but **security must be handled explicitly**.


---

### Import/Export Customization

TreeNode Framework provides a robust and extensible system for importing and exporting tree-structured data.  

The default functionality covers the most common use cases, but real-world projects often require custom validation, enrichment, conflict handling, or filtering during these operations.  
This section explains how to safely customize the import and export processes without breaking core tree consistency.

| Feature | Description |
|:--------|:------------|
| **Import** | Handled by `TreeNodeImporter`, supports CSV, TSV, JSON, XLSX, and YAM. |
| **Export** | Handled by `TreeNodeExporter`, outputs tree data ordered by structure. |
| **Streaming Export** | Memory-efficient export even for large trees via `StreamingHttpResponse`. |
| **Cache Management** | Tree cache is automatically cleared after import or structural changes. |

You can extend or override the import process by subclassing the importer or hooking into model-level methods.

Common customization scenarios:

- **Preprocessing**: Validate or transform records before creating nodes.
- **Conflict Resolution**: Define how to handle cases where imported IDs already exist.
- **Postprocessing**: Enrich newly created nodes (e.g., setting computed fields).

For example, you can make validating imported records:

```python
from treenode.importer import TreeNodeImporter

class CustomCategoryImporter(TreeNodeImporter):
    
    def process_record(self, record):
        if not record.get("name"):
            raise ValueError("Each node must have a non-empty name.")
        return super().process_record(record)
```

Now you can use:

**admin.py**

```python
class CategoryAdmin(TreeNodeModelAdmin):
    importer_class = CustomCategoryImporter
```

Likewise you can customize what data gets exported and how. Typical scenarios:

- **Filtering nodes**: Export only active or visible nodes.
- **Altering output format**: Include additional computed fields.
- **Partial tree export**: Export subtrees based on specific business logic.

Use class  `exporter_class`  attribute of TreeNodeModelAdmin class:

```python
CategoryAdmin(TreeNodeModelAdmin):
    exporter_class = CustomCategoryExporter
```

!!! tip "Best Practices"

    - Always validate imported data to maintain tree consistency.
    - Prefer enriching nodes after insertion, not by modifying core import logic.
    - Be cautious with conflict handling: duplicated IDs must be addressed explicitly.
    - If adding new fields to exports, ensure they are serialized safely for all supported formats.
    - Keep custom import/export logic isolated and document it clearly.

---
