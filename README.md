# Treenode Framework
**A hybrid open-source framework for working with trees in Django**

[![Tests](https://github.com/TimurKady/django-fast-treenode/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/TimurKady/django-fast-treenode/actions/workflows/test.yaml)
[![Docs](https://readthedocs.org/projects/django-fast-treenode/badge/?version=latest)](https://django-fast-treenode.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/django-fast-treenode.svg)](https://pypi.org/project/django-fast-treenode/)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-fast-treenode/)
[![Sponsor](https://img.shields.io/github/sponsors/TimurKady)](https://github.com/sponsors/TimurKady)

## About The Treenode Framework
### Overview

**Treenode Framework** is an advanced tree management system for Django applications. It is designed to handle large-scale, deeply nested, and highly dynamic tree structures while maintaining excellent performance, data integrity, and ease of use.

Unlike traditional solutions, **Treenode Framework** is built for serious real-world applications where trees may consist of:

- Number nodes to 50-100 thousands nodes,
- Nesting depths to 1,000 levels,
- Complex mutation patterns (bulk moves, merges, splits),
- Real-time data access via API.

Its core philosophy: **maximum scalability, minimum complexity**.

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

Due to its high performance and ability to support deep nesting and large tree sizes, the `django-fast-treenode` package can be used for any tasks that involve the use of tree-like data, with virtually no restrictions.

### Where Massive Trees Really Matter?

**Treenode Framework** is designed to handle not only toy examples, but also real trees with strict requirements for the number of nodes and their nesting.

Typical applications include:

- **Digital Twin Systems** for industrial asset management (plants, machinery, vehicles), where full structural decomposition is critical for maintenance planning and cost optimization.
- **Decision Support Systems** in medicine, law, and insurance, where large and dynamic decision trees drive critical reasoning processes.
- **AI Planning Engines** based on hierarchical task networks, allowing intelligent agents to decompose and execute complex strategies.
- **Biological and Genetic Research**, where large phylogenetic trees model evolutionary relationships or genetic hierarchies.

In all these domains, scalable and fast tree management is not a luxury — it's a necessity.

### Why Treenode Framework?
At the moment, `django-fast-treenode` is, if not the best, then one of the best packages for working with tree data under Django.

- **High performance**: [tests show](docs/about.md#benchmark-tests) that on trees of 5k-10k nodes with a nesting depth of 500-600 levels, **Treenode Framework** (`django-fast-treenode`) shows **performance 4-7 times better** than the main popular packages.
- **Flexible API**: today contains the widest set of methods for working with a tree in comparison with other packages.
- **Convenient administration**: the admin panel interface was developed taking into account the experience of using other packages. It provides convenience and intuitiveness with ease of programming.
- **Scalability**: **Treenode Framework** suitable for solving simple problems such as menus, directories, parsing arithmetic expressions, as well as complex problems such as program optimization, image layout, multi-step decision making problems, or machine learning..
- **Lightweight**: All functionality is implemented within the package without heavyweight dependencies such as `djangorestframework` or `django-import-export`.
- **Optional JWT authentication**: enable token-based protection for the API with a single setting.

All this makes **Treenode Framework** a prime candidate for your needs.

## Quick Start
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
  from treenode.models import TreenodeModel

  class MyTree(TreenodeModel):
    name = models.CharField(max_length=255)
    display_field = "name"
  ```

- Open **admin.py** and create a model for the admin panel
  ```
  from django.contrib import admin
  from treenode.admin import TreenodeModelAdmin
  from .models import MyTree

  @admin.register(MyTree)
  class MyTreeAdmin(TreenodeModelAdmin):
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

## Documentation
Full documentation is available at **[ReadTheDocs](https://django-fast-treenode.readthedocs.io/)**.

Quick access links:
* [Installation, configuration and fine tuning](https://django-fast-treenode.readthedocs.io/installation/)
* [Model Inheritance and Extensions](https://django-fast-treenode.readthedocs.io/models/)
* [Working with Admin Classes](https://django-fast-treenode.readthedocs.io/admin/)
* [API Reference](https://django-fast-treenode.readthedocs.io/api/)
* [Import & Export](https://django-fast-treenode.readthedocs.io/import_export/)
* [Caching and working with cache](https://django-fast-treenode.readthedocs.io/cache/)
* [Migration and upgrade guide](https://django-fast-treenode.readthedocs.io/migration/)

Your wishes, objections, comments are welcome.

## License
Released under [MIT License](https://github.com/TimurKady/django-fast-treenode/blob/main/LICENSE).

## Credits
Thanks to everyone who contributed to the development and testing of this package, as well as the Django community for their inspiration and support. 

Special thanks to [Fabio Caccamo](https://github.com/fabiocaccamo) for the idea behind creating a fast Django application for handling hierarchies.

Also special thanks to everyone who supports the project with their [sponsorship donations](https://github.com/sponsors/TimurKady).

