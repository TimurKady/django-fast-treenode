# Treenode Framework
**A hybrid open-source framework for working with trees in Django**

Welcome to the **django-fast-treenode** documentation!

---

### Overview

**Treenode Framework** is an advanced tree management system for Django applications.  It is designed to handle large-scale, deeply nested, and highly dynamic tree structures while maintaining excellent performance, data integrity, and ease of use.

Unlike traditional solutions, **Treenode Framework** is built for serious real-world applications where trees may consist of:

- Number nodes to 50-100 thousands nodes,
- Nesting depths to 1,000 levels,
- Complex mutation patterns (bulk moves, merges, splits),
- Real-time data access via API.

Its core philosophy: **maximum scalability, minimum complexity**.

---

### Where Massive Trees Really Matter?

**Treenode Framework** is designed to handle not only toy examples, but also real trees with strict requirements for the number of nodes and their nesting.

Typical applications include:

- **Digital Twin Systems** for industrial asset management (plants, machinery, vehicles), where full structural decomposition is critical for maintenance planning and cost optimization.
- **Decision Support Systems** in medicine, law, and insurance, where large and dynamic decision trees drive critical reasoning processes.
- **AI Planning Engines** based on hierarchical task networks, allowing intelligent agents to decompose and execute complex strategies.
- **Biological and Genetic Research**, where large phylogenetic trees model evolutionary relationships or genetic hierarchies.

In all these domains, scalable and fast tree management is not a luxury — it's a necessity.

### Why TreeNode Framework?
At the moment, django-fast-treeenode is, if not the best, then one of the best packages for working with tree data under Djangjo.

- **High performance**: [tests show](about.md#benchmark-tests) that on trees of 5k-10k nodes with a nesting depth of 500-600 levels, `django-fast-treenode` shows **performance 4-7 times better** than the main popular packages.
- **Flexible API**: today `django-fast-treenode` contains the widest set of methods for working with a tree in comparison with other packages.
- **Convenient administration**: the admin panel interface was developed taking into account the experience of using other packages. It provides convenience and intuitiveness with ease of programming.
- **Scalability**: `django-fast-treenode` suitable for solving simple problems such as menus, directories, parsing arithmetic expressions, as well as complex problems such as program optimization, image layout, multi-step decision making problems, or machine learning..
- **Lightweight**: All functionality is implemented within the package without heavyweight dependencies such as `djangorestframework` or `django-import-export`.

All this makes `django-fast-treenode` a prime candidate for your needs.

### Quick Start
To get started quickly, you need to follow these steps:

- Simply install the package via `pip`:
  ```sh
  pip install django-fast-treenode
  ```
- Once installed, add `'treenode'` to your `INSTALLED_APPS` in **settings.py**:
  ```python {title="settings.py"}
  INSTALLED_APPS = [
      ...
      'treenode',
      ...
  ]
  ```

- Open **models.py** and create your own tree class:
  ```
  from treenode.models import TreeNodeModel

  class MyTree(TreeNodeModel):
    name = models.CharField(max_length=255)
    display_field = "name"
  ```

- Open **admin.py** and create a model for the admin panel
  ```
  from django.contrib import admin
  from treenode.admin import TreeNodeModelAdmin
  from .models import TestNode

  @admin.register(TestNode)
  class EntityAdmin(TreeNodeModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
  ```

- Then, apply migrations:
  ```sh
  python manage.py makemigrations
  python manage.py migrate
  ```

- Run server
  ```sh
  python manage.py runserver
  ```

Everything is ready, enjoy 🎉!

---

### Key Features
#### Common operations
The `django-fast-treenode` package supports all the basic operations needed to work with tree structures:

- Extracting **ancestors** (queryset, list, pks, count);
- Extracting **children** (queryset, list, pks, count);
- Extracting **descendants** (queryset, list, pks, count);
- Extracting a **family**: ancestors, the node itself and its descendants (queryset, list, pks, count);
- Enumerating all the nodes (queryset, dicts);
- **Adding** a new node at a **certain position** on the tree;
- Automatic **sorting of node order** by the value of the specified field;
- **Deleting** an node;
- **Pruning**: Removing a whole section of a tree;
- **Grafting**: Adding a whole section to a tree;
- Finding the **root** for any node;
- Finding the **lowest common ancestor** of two nodes;
- Finding the **shortest path** between two nodes.

Due to its high performance and ability to support deep nesting and large tree sizes, the `django-fast-treeode` package can be used for any tasks that involve the use of tree-like data, with virtually no restrictions.

#### Additional features
The `django-fast-treenode` package has several additional features, some of which are unique to similar packages:

- **API-first** support (without DRF);
- Flexible **Admin Class**: tree widgets support and drag and drop functionality;
- **Import and Export** tree data to/from file (CSV, JSON, TSV, XLSX, YAML).

All these features are available "out of the box".

---



---

### Supported Versions
#### Supported Django Versions

The project supports Django versions starting from **Django 4.0** and higher:

- Django 4.0, 4.1, 4.2 (LTS)
- Django 5.0
- Django 5.1
- Django 5.2 (support is ready and tested)

The project is designed for long-term compatibility with future Django versions without requiring architectural changes.

#### Supported Databases and Minimum Versions

All SQL queries are adapted through a universal compatibility layer, ensuring support for major databases without the need to rewrite SQL code.

| Database         | Minimum Version | Status              | Notes |
|------------------|------------------|---------------------|-------|
| **PostgreSQL**    | ≥ 9.4            | Full tested     | Recommended ≥ 12 |
| **MySQL**         | ≥ 8.0            | Partially tested | |
| **MariaDB**       | ≥ 10.2.2         | Not tested      | |
| **SQLite**        | ≥ 3.25.0         | Partially tested | |
| **Oracle**        | ≥ 12c            | Full tested     | Recommended ≥ 19c |
| **MS SQL Server** | ≥ 2012           | Partially tested| |


The project is **ready for production use** across all modern versions of Django and major relational databases without manual SQL corrections.

### License
Released under the [MIT License](https://github.com/TimurKady/django-fast-treenode/blob/main/LICENSE).
