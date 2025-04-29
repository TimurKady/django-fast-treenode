## TreeNode Cache Management

### Caching Strategy

The caching mechanism in TreeNode Framework has undergone a clear evolution from a naive first-generation strategy to a robust, controlled system.

Initially, it used Django's default cache to store individual query results. This was simple and fast, but quickly led to uncontrolled memory growth, especially under frequent tree operations, eventually degrading overall cache performance.

In the current version, caching is managed through a fixed-size FIFO queue, shared across all TreeNodeModel instances. This ensures that the oldest entries are automatically discarded when the memory limit is reached.

While FIFO is not the most sophisticated strategy, it strikes an effective balance between performance and simplicity, providing predictable behavior and stable memory usage under high load — a significant improvement over the earlier unbounded approach.

---

### Key Features

**Global Cache Limit**: The setting `TREENODE_CACHE_LIMIT` defines the maximum cache size (in MB) for **all models** inheriting from `TreeNodeModel`. Default is **100MB** if not explicitly set in `settings.py`.

**settings.py**
``` python
TREENODE_CACHE_LIMIT = 100
```

**Automatic Management**. In most cases, users don’t need to manually manage cache operations.All methods that somehow change the state of models reset the tree cache automatically.

**Manual Cache Clearing**. If for some reason you need to reset the cache, you can do it in two ways:

- **Clear cache for a single model**: Use `clear_cache()` at the model level:
    ```python
    MyTreeNodeModel.clear_cache()
    ```
- **Clear cache for all models**: Use the global `treenode_cache.clear()` method:
    ```python
    from treenode.cache import treenode_cache
    treenode_cache.clear()
    ```

---

### Ceche API

#### `@cached_method` Decorator

The `@cached_method` decorator is available for caching method results in **class and instance methods** of models inheriting from `TreeNodeModel`. This decorator helps optimize performance by reducing redundant computations.

```python
from treenode.cache import cached_method
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):
    name = models.CharField(max_length=50)

    @cached_method
    def my_tree_method(self):
        # Your code is here
```

In this example, `my_tree_method()` is cached.

**Important:** The decorator should **only** be used with `TreeNodeModel` subclasses. Applying it to other classes will cause unexpected behavior.


#### Accessing Cache via `treenode_cache`

A global cache instance `treenode_cache` provides direct cache manipulation methods, allowing you to generate cache keys, store, retrieve, and invalidate cached values.

Methods available in `treenode_cache`:

#### generate_cache_key()
Generates a unique cache key for caching method results. The key is based on model name, method name, object identifier, and method parameters.

```python
cache_key = treenode_cache.generate_cache_key(
    label=Category._meta.label,  # Model label
    func_name=self.<The method you are in>.__name__,
    unique_id=42,   # This can be the object.pk. In a desperate situation, use id(self)
    attr="some string value"
)
```
This ensures that the cache key follows Django's conventions and remains unique.

#### set()
Stores a value in the cache.

```python
treenode_cache.set(cache_key, {'name': 'Root', 'id': 1})
```
This caches a dictionary object under the generated key.

#### get()
Retrieves a cached value by its cache key.

```python
cached_value = treenode_cache.get(cache_key)
if cached_value is None:
    cached_value = compute_expensive_query()
    treenode_cache.set(cache_key, cached_value)
```

#### invalidate()
Removes all cached entries for a **specific model**.

```python
treenode_cache.invalidate(Category._meta.label)
```
This clears all cache entries related to `Category` instances.

#### clear()
Clears **all** cached entries in the system.

```python
treenode_cache.clear()
```
This completely resets the cache, removing **all stored values**.

Best Practices:

- **Always use `generate_cache_key()`** instead of hardcoding cache keys to ensure consistency.
- **Use `invalidate()` instead of `clear()`** when targeting a specific model’s cache.
- **Apply `@cached_method` wisely**, ensuring it is used **only for** `TreeNodeModel`-based methods to avoid conflicts.
- **Be mindful of cache size**, as excessive caching can lead to memory bloat.

By leveraging these caching utilities, `django-fast-treenode` ensures efficient handling of hierarchical data while maintaining high performance.

