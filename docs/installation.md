## Installation

This section describes the process of installing TreeNode Framework into a new Django project or upgrading previous versions of the package, including basic requirements, setup steps, and database migration.
Specifically, it covers ways to migrate existing projects implemented using alternative applications to TreeNode Framework.

### Installation Steps
If you are installing `django-fast-treenode` for the first time, the process is straightforward. Simply install the package via `pip`:

```sh
pip install django-fast-treenode
```

If you are upgrading to a new version of `django-fast-treenode` or switching from `django-treenode`, it is essential to run migrations to ensure data consistency:

```sh
pip install --upgrade django-fast-treenode
```

Once installed, add `'treenode'` to your `INSTALLED_APPS` in **settings.py**:

```python
INSTALLED_APPS = [
    ...
    'treenode',
    ...
]
```

Now you can start fine-tuning the Treenode Framework or skip the next step and start [working with your own models](models.md#modelinheritance).

---

### Initial Configuration

In the standard delivery, TreeNode Framework does not require additional configuration. All key parameters are optimized for working out of the box.
Together, some settings that affect the operation of **Treenode Framework** can be changed by setting their values ​​in your project's settings file **settings.py**.

#### Cache Size Allocation (`TREENODE_CACHE_LIMIT`)

This setting controls the memory allocation for caching all tree model instances. 

The cache stores all tree-related data for models that inherit from TreeNodeModel. By default, the value of the `TREENODE_CACHE_LIMIT` parameter is 100 MB.

You can control the cache size with `TREENODE_CACHE_LIMIT` by specifying its limit in megabytes. For example:

```python
TREENODE_CACHE_LIMIT = 256
```

For more details on how caching works and how to fine-tune its behavior, refer to the [Caching and Cache Management](cache.md)  Guide.


#### The length on Materialized Path segment (`TREENODE_SEGMENT_LENGTH`)

When constructing a node path (for example: `000.001.003`), each path segment (`"000"`, `"001"`, `"003"`) has a fixed length, determined by the `TREENODE_SEGMENT_LENGTH` constant.

By default, the segment length is **3 characters**. This allows each parent node to have up to **4096 child nodes**. If you need to support more children at a single level, you can increase the value of `TREENODE_SEGMENT_LENGTH` by adding the appropriate setting to your project's **settings.py**:

```python
TREENODE_SEGMENT_LENGTH = 4
```

!!! warning
    **Be careful**: increasing `TREENODE_SEGMENT_LENGTH` causes the materialized path field (which is indexed by the database) to become longer. Due to maximum index size limitations in most database management systems (DBMS), this can lead to database-level errors when the tree is deeply nested.

In practice, for most use cases, a value of 3 is optimal.
It allows efficient work with trees of 5,000–10,000 nodes, while supporting a maximum depth of approximately 1000 levels.

Changing the segment length affects the balance between the width and depth of the tree:

- A smaller value (e.g., 2) allows for greater depth but reduces the number of children per node (up to 256).
- A larger value (e.g., 5) increases the number of possible children (up to 1,048,576) but reduces the maximum depth due to the increased path string size.


| TREENODE_SEGMENT_LENGTH | Children per node (max) | Depth limit (aprox.) |
|:-----------------------:|-------------------------:|:-------------------:|
|            2            |                      256 | ~3000 levels |
|            3            |                     4096 | ~1000 levels |
|            4            |                   65,536 |  ~250 levels |
|            5            |                1,048,576 |  ~100 levels |

Now the Treenode Framework is ready to work. You can proceed to describe your Django models by inheriting them from the abstract TreeNodeModel class and extending them according to the task you are solving.

#### Login-based security to models APIs (`TREENODE_API_LOGIN_REQUIRED`)

This setting enables global [API security for all tree models](apifirst.md) at once. When set to `True`, applies login-based security to all tree model APIs. Defaults to False

**settings.py**:

```python
TREENODE_API_LOGIN_REQUIRED = True
```
This forces all TreeNode Framework APIs to require authentication.

If [`api_login_required`](models.md#clsapi_login_required) is set for a model, `api_login_required` takes precedence. If the setting does not exist at the model level, the global setting is used.

