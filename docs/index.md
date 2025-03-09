# Django Fast TreeNode
**A Powerful Solution for Hierarchical Data Management**

Welcome to the **django-fast-treenode** documentation!

## Overview

**Django Fast TreeNode** is a specialized Django package designed to efficiently handle hierarchical data structures. It leverages **combining Adjacency List and Closure Table** to optimize querying and management of tree-like structures, making it an excellent choice for applications that require fast traversal, retrieval, and manipulation of nested relationships.

The package is particularly useful in scenarios such as:

- **Categories and taxonomies**: Manage product categories, tags, and classification systems.
- **Menus and navigation**: Create tree-like menus and nested navigation structures.
- **Forums and comments**: Store threaded discussions and nested comment chains.
- **Geographical data**: Represent administrative divisions, regions, and areas of influence.
- **Organizational and Business Structures**: Model company hierarchies, business processes, employees and departments.

In all applications, `django-fast-treenode` models show excellent **performance** and **stability**.

## Key Features

1. **Efficient Tree Operations**:
    * Supports fast retrieval of ancestors, descendants, and siblings.
    * Uses a **closure table approach** for optimal query performance.

2. **Django ORM Integration**:
    * Extends Django’s `models.Model`, making it easy to integrate into existing applications.
    * Custom manager (`TreeNodeManager`) provides useful tree-related query optimizations.


3. **Query Optimization via Closure Table**
    * Instead of naive recursive queries, the package precomputes relationships in a separate closure table.This allows you to run constant-time queries for retrieval using a **single database query**:
        * Ancestors (`get_ancestors()`),
        * Depth (`det_depth()`),
        * Descendants (`get_descendants()`),
        * Family (`get_family()`),
        * Materialized Path(`get_breadcrumbs()` and `get_path()`),
        * Roots (`get_root()`),
        * Siblings (`get_siblings()`) and so on.

4. **Automatic Ordering and Priority Management**:
    * Nodes can be assigned priority values for custom sorting.
    * Provides automatic ordering based on a **materialized path**.

5. **Admin Interface Enhancements**:
    * Supports multiple tree display modes in the Django Admin:
        * **Indentation mode** (classic hierarchical view)
        * **Breadcrumbs mode** (for easy navigation)
        * **Accordion mode** (collapsible structures)
    * Uses a **custom admin widget** (`TreeWidget`) to enhance usability.


6. **Caching for Performance**:
    * Uses Django’s caching framework to optimize frequently accessed tree operations.
    * Cached tree methods reduce redundant computations.


7. **Bulk Operations Support**:
    * Implements efficient **bulk creation** of nodes.
    * Provides methods for **batch updates** and **tree rebuilding**.

By leveraging combining with Closure Tables, it offers superior performance compared to traditional tree structures.

## Use Cases and Benefits

### When to Use Django Fast TreeNode?
- **You need a nested structure with frequent reads**: Closure tables provide **fast lookups** compared to recursive Common Table Expressions (CTEs).
- **You want an easy-to-use Django model**: The package **extends Django ORM** and integrates seamlessly.
- **You require hierarchical display in Django Admin**: The **custom admin integration** makes managing trees much easier.

### Benefits Over Other Approaches
- **Better than adjacency lists** (which require multiple queries for deep trees).
- **More efficient than recursive queries** (which can be slow on large datasets).
- **Scalable for large trees** (by leveraging precomputed paths and caching).

Django Fast TreeNode is a powerful and efficient package for managing hierarchical data in Django applications. Its seamless ORM integration and Django Admin support make it a great choice for developers looking to implement **fast, scalable** tree-based data structures.

## Contents
- [About the Project](about.md)
- [Installation, Configuration, and Fine-Tuning](installation.md)
- [Model Inheritance and Extensions](models.md)
- [Working with Admin Classes](admin.md)
- [API Reference](api.md)
- [Import & Export](import_export.md)
- [Caching and Cache Management](cache.md)
- [Migration and Upgrade Guide](migration.md)
- [Roadmap](roadmap.md)

## Links
- [Issues](https://github.com/TimurKady/django-fast-treenode/issues)
- [Pull Requests](https://github.com/TimurKady/django-fast-treenode/pulls)
- [Discussions](https://github.com/TimurKady/django-fast-treenode/discussions)

## License
Released under the [MIT License](https://github.com/TimurKady/django-fast-treenode/blob/main/LICENSE).
