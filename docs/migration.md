## Migrations Guide
### Update django-fast-treenode version 2.1 and less
TreeNode Framework 3.x introduces significant architectural changes aimed at improving performance, scalability, and bulk operation safety.

The internal structure of the models has changed:

- Field `tn_parent` is replaced by `parent`.
- Field `tn_priority` is replaced by `priority`.
- Closure tables (`ClosureModel`) are no longer used.

This requires a simple but **careful migration process** to preserve data integrity.

####  Step 1. Backup your database

Before starting the upgrade process, **create a full backup** of your database:

```bash
python manage.py dumpdata > backup.json
```
or use admin panel for export data or database-level tools like `pg_dump`, `mysqldump`, etc.


!!! important
    Migration will drop obsolete tables and fields. A backup is mandatory to avoid irreversible
    data loss.


### Step 2. Upgrade the package

Install the latest version of TreeNode Framework:

```bash
pip install --upgrade django-fast-treenode
```

#### Step 3. Create migrations

Generate new migrations for your application:

```bash
python manage.py makemigrations your_app
```

Django will detect the following changes:

- Rename suggestions:
    - `tn_parent` → `parent`
    - `tn_priority` → `priority`
- Warning about model/table deletion:
    - Django may suggest deleting the closure table previously used for managing ancestor relationships.

!!! warning
    1. **Accept the renaming operations**. This preserves the structure of your tree.
    2. **Accept the ClosureModel table deletion**. There is no need for it anymore.


#### Step 4. Apply migrations

Apply the generated migrations:

```bash
python manage.py migrate
```

This will update the database schema without affecting existing data integrity if steps above were followed correctly.

#### Step 5. Rebuild tree paths (optional but recommended)

Although the migration preserves structural links, it is recommended to **rebuild** materialized paths and depths to ensure full consistency.

Launch Django shell:

```bash
python manage.py shell
```

Then execute:

```python
YourTreeNodeModel.rebuild()
```

!!! note
    This ensures all path and depth values are refreshed according to the new model logic.

#### Step.6 Final Check

After completing the migration:

- Verify that all parent/child relationships are intact.  
- Check that tree traversal (get descendants, get ancestors) works properly.  
- Validate that no old `tn_` fields remain in your models or database.

#### Possible Issues and Solutions

| Issue                             | Reason                               | Solution                        |
|:----------------------------------|:-------------------------------------|:--------------------------------|
| Django does not offer to rename fields | Migration autogeneration missed changes | Manually edit migration files to use `RenameField` |
| Loss of parent/child relationships | Ignored rename prompts | Rollback and repeat migration with renames accepted |
| Errors about missing Closure tables | Old code references deleted models | Remove or replace old closure-related logic |
| Unexpected field deletions        | Manually modified models during migration | Always verify `makemigrations` output carefully |


Migration is safe and straightforward if you follow this guide carefully.

---

### Migration from django-treenode

Migrating from **django-treenode** to the new **TreeNode Framework** is usually a **smooth and straightforward** process. In general, migration from **django-treenode** is similar to upgrading from an older version of **django-fast-treenode**. The internal concepts are very similar. Most of your codebase will continue to work with minimal or no changes.

#### Step 1. Upgrade the package

Uninstall `django-treenode`, install TreeNode Framework.

```bash
pip uninstall django-treenode
pip install django-fast-treenode
```

#### Step 2. Apply database migrations

After installing the new package, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

This will update the model fields and drop deprecated structures if necessary.

#### Step 3. **Review your code**

Unlike django-treenode, TreeNode Framework **does not support fields with the `tn_` prefix** (such as `tn_parent`, `tn_priority`).

You should search your codebase for any **direct references** to `tn_` fields.

!!! tip  
    In most cases, you should replace direct field access with the **official model methods** to ensure forward compatibility.

#### Step 4. Adjust admin classes (if customized):

If you had customized Django Admin integration based on `django-treenode`,  
you may need minor adjustments to fieldsets or list display settings to reflect the new field names.

#### Step 5. **Test your application**

After migration, verify:

- Parent/child relationships are preserved
- Tree traversal methods (get descendants, ancestors) work correctly
- No code references missing `tn_` fields

!!! hint
    If you always adhere to the documented APIs, migrating or upgrading any package or library should always succeed without major issues.

---

### Migration from other packege
Migration from other packages is not as seamless as with `django-treebeard`, which is probably understandable. However, `django-fast-treenode` has been specially tweaked so that such migration requires minimal effort, including minimal changes to your project code.
Below is a guide on how to migrate to `django-fast-treenode` from other packages using a project using `django-treebeard` as an example. Migration from other packages will involve similar steps.

#### Step 1: Export existing data
Launch the Python console:

```bash
python manage.py shell
```

Run the following code to export the tree structure:
```python
from yourapp.models import Category
import json

data = []

def export_tree(node):
    children = node.get_children()
    return {
        "id": node.id,
        "parent": node.get_parent().id if node.get_parent() else None,
        "name": node.name,
        # Continue the list by inserting the required model fields
        # Do not export the `children` field
    }

roots = Category.objects.filter(depth=1)  # treebeard root nodes
for root in roots:
    data.append(export_tree(root))

with open("tree_data.json", "w") as f:
    json.dump(data, f, indent=4)
```

This code exports your structure to `tree_data.json` file. JSON preserves the id → parent relationship, but without children.

Now clear the table:
```python
Category.objects.all().delete()
```
Remove `django-treebeard` if it is installed:
```bash
pip uninstall django-treebeard
```
Install `django-fast-treenode`:
```bash
pip install django-fast-treenode
```

Before you start the migration, it is important to make sure **you have a backup of your database**, as the tree storage structure will change.

#### Step 2: Preparing for Migration
If you have a model in your project that uses `treebeard`, it probably looks like this:
```python
from treebeard.mp_tree import MP_Node

class Category(MP_Node):
    name = models.CharField(max_length=255)
```
Now we need to adapt it for `django-fast-treenode`. Change the model to use `TreeNodeModel` instead of `MP_Node`:
```python
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):
    name = models.CharField(max_length=255)

    treenode_display_field = "name"
    treenode_sort_field = "None"
```
Be sure to add `treenode_display_field` as `django-fast-treenode` uses it to display nodes in the admin panel. 

The `treenode_sort_field` attribute specifies the tree sorting order. The default value of this field is `None`. It will sort by the internal field `priority`.

The `priority` value will be generated automatically if not specified during import. It will either be set as nodes are inserted into the tree (in the order in which the nodes will appear in the imported data), or after they are inserted, depending on the results of sorting by the field specified in the `treenode_sort_field` attribute.

> Note: sorting functions are available for `django-tree-node` version 2.3 and higher.

#### Step 3: Update the code
The `django-fast-treenode` package contains the full set of methods you are used to. But the methods for working with the tree are slightly different. For example:

|**django-treebeard** | **django-fast-treenode** |**Features of use**|
|---------------------|----------------------|----------------------|
| The `pos` parameter in `add_sibling()` and `move()` methods |  The parameter `pos` has the name `position` | • The `position` parameter in `django-fast-treenode` always consists of two parts separated by <br>`-`: the first part determines the insertion method (_first, left, right, last, sorted_), the second — the placement type (_child, sibling_). <br> • Instead of a string format, you can also pass position as an integer indicating the exact position of the node in the list.|
|`get_siblings()`, `get_ancestors()` end ect. | Similar methods have parameters `include_self` and `depth` |• The `include_self` parameter specifies whether to include the node itself in the selection. <br> • The  `depth` parameter specifies the depth of the search. |
|`move(target, pos)` metiod| The method `move()` has the name `move_to(target, position)` | - |

As you can see, unlike treebeard, django-fast-treenode provides more features, allowing you to use familiar methods more flexibly.

For more details, refer to the `django-fast-treenode` documentation and update your code accordingly


#### Step 4: Create Migrations
After changing the model, new migrations need to be created and applied.

```bash
python manage.py makemigrations
python manage.py migrate
```

After a successful migration, you can remove references to `django-treebeard` in `requirements.txt` and `INSTALLED_APPS` if they were there.

#### Step 5:  Data Import
Now start the server.
   ```bash
   python manage.py runserver
   ```

Go to Django Admin and import data into your model from the previously saved file. `django-fast-treenode` will do everything automatically. Check if the tree structure is displayed correctly. 

Moreover, the import will preserve the `id` of all nodes, which will ensure that the values of the keys referencing your model are unchanged.

---

Now your project has completely migrated from `django-treebeard` to `django-fast-treenode`. Your tree is more performant and easier to use, and your code is cleaner and more flexible.
