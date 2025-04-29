## About the project
### Approach

In any system that manages hierarchical data, the choice of internal representation is critical to achieving a balance between **performance**, **consistency**, and **development simplicity**.

TreeNode Framework follows the philosophy that no single tree management method is ideal for all tasks. Instead, it embraces a **hybrid approach**, combining multiple classic methods to maximize their strengths while minimizing their weaknesses.

The goal is simple: **fast reads, reliable updates, scalable growth**, and **minimal database load** even when dealing with trees containing tens of thousands of nodes.

---

### History

The original inspiration for this framework came from the outstanding work of **[Fabio Caccamo](https://github.com/fabiocaccamo)**.

Fabio's project, **[django-treenode](https://github.com/fabiocaccamo/django-treenode)**, introduced an elegant concept: using the **Adjacency List** method for tree storage, combined with **precalculated values** and aggressive **query caching**.  
This made read operations extremely fast — often achievable with a single lightweight database call or no call at all, if the cache was warm.

The original application had several undeniable advantages over traditional recursive models:

- Efficient selections without complex recursive queries
- Smart caching for predictable response times
- Deep integration with Django ORM

However, certain architectural trade-offs also became apparent:

- The **precalculation strategy** introduced **heavy overhead** for write operations, particularly when adding new nodes.
- The reliance on **Django signals** for tree maintenance led to **instability** when using **bulk operations** (e.g., bulk_create, bulk_update).
- **Node ordering inside a parent** was not inherently supported, leading to difficulties when tree branches needed precise internal ordering based on priorities.

In short, the **excellent debut idea** deserved further development to fully realize its potential at scale.

TreeNode Framework was born from this insight — preserving the best aspects of the original while rethinking the internal mechanisms for greater robustness.

---

### Why a Hybrid Approach

After extensive experimentation with different tree models (Adjacency List, Materialized Path, Nested Set, Closure Table), it became clear that **no single method** could meet all practical requirements.

- **Adjacency List** is simple and efficient for single node queries, but recursive traversal is expensive.
- **Materialized Path** allows fast subtree retrieval but complicates updates during node movement.
- **Nested Set** is excellent for entire subtree reads but very costly for inserts and structural changes.
- **Closure Table** is flexible but complex and storage-heavy.

TreeNode Framework chose to combine:

- **Materialized Path** for efficient sorting, retrieval, and traversal
- **Adjacency Table** (simple `parent_id` linkage) for lightweight parent/child management
- **Dynamic caching and task queues** to offload expensive operations

This hybrid model ensures:

- **Fast reads** (entire subtree retrievals in one indexed query)
- **Predictable writes** (insertions and movements with minimal locking)
- **Safe bulk operations** (no reliance on Django signals or ORM events)
- **Flexible extension points** for future scaling.

---

### Architecture Overview

TreeNode Framework's architecture is built around a clear separation of concerns:

| Component        | Responsibility                           |
|:-----------------|:-----------------------------------------|
| **TreeNodeModel** | Base model handling structural fields (`parent_id`, `_path`, `_depth`, `priority`) |
| **SQL Queue (sqlq)** | Defers expensive updates into efficient batch SQL operations |
| **Task Queue (tasks)** | Manages delayed tree maintenance tasks (e.g., path recalculation) |
| **Cache Layer** | Maintains quick access to tree fragments without hitting the database |
| **Admin Extensions** | Provides drag-and-drop and advanced UI functionality for Django Admin |
| **API Generator** | Enables API-First development with automatic endpoint creation for any tree model |

Each layer has a minimal surface area, designed for maximum composability and customization.

#### Key Concepts:

- **Deferred Execution**:
  Write-heavy operations (such as bulk inserts) do not immediately trigger costly recalculations. Instead, recalculations are queued and executed efficiently afterward.

- **Materialized Path Rebuilding**:
  When a node is inserted or moved, the system can selectively rebuild only the affected subtree — avoiding full-tree recalculations.

- **Smart SQL**:
  Updates and reconstructions of `_path` and `_depth` are done through direct SQL (`WITH RECURSIVE`) rather than slow per-object ORM updates.

- **Queue Safety**:
  The SQL queue (`sqlq`) and Task queue (`tasks`) ensure that tree state remains consistent even under concurrent modifications.

- **Optional Background Execution**:
  For very large trees, recalculations and cache invalidations can be moved into background threads or task queues (such as Celery), providing further scalability.

- **Extensibility by Design**:
  Developers can extend Admin behavior, customize API responses, or override parts of the TreeNode behavior without touching core logic.

---

### Summary

TreeNode Framework represents a pragmatic evolution of tree management ideas in Django.

It brings together the best theoretical concepts from academic tree models and real-world practices from high-load production systems, combining them into a clean, lightweight, and efficient framework that stays true to Django's principles.

Whether you are building a product catalog, an organizational chart, or any complex hierarchical structure, TreeNode Framework offers you a robust, flexible, and future-proof foundation.

