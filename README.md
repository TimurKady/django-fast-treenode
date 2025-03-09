# Django-fast-treenode 
**Combining Adjacency List and Closure Table for Optimal Performance**

|tests| |docs| |pypi|

.. |tests| image:: https://github.com/TimurKady/django-fast-treenode/actions/workflows/test.yaml/badge.svg?branch=main
   :target: https://github.com/TimurKady/django-fast-treenode/actions/workflows/test.yaml

.. |docs| image:: https://readthedocs.org/projects/django-fast-treenode/badge/?version=latest
   :target: https://django-fast-treenode.readthedocs.io/en/latest/

.. |pypi| image:: https://img.shields.io/pypi/v/django-fast-treenode.svg
   :target: https://pypi.org/project/django-fast-treenode/

**Django Fast TreeNode** is a high-performance Django application for working with tree structures, combining **Adjacency List** and **Closure Table** models. Each **TreeNodeModel** instance maintains two synchronized tables, enabling most operations to be performed with a single database query.

## Features
- **Hybrid storage model**: Combines Adjacency List and Closure Table for optimal performance.
- **Custom caching system**: A built-in caching mechanism, specifically designed for this package, significantly boosts execution speed.
- **Efficient queries**: Retrieve ancestors, descendants, breadcrumbs, and tree depth with only one SQL queriy.
- **Bulk operations**: Supports fast insertion, movement, and deletion of nodes.
- **Flexibility**: Fully integrates with Django ORM and adapts to various business logic needs.
- **Admin panel integration**: Full compatibility with Django's admin panel, allowing intuitive management of tree structures.
- **Import & Export functionality**: Built-in support for importing and exporting tree structures in multiple formats (CSV, JSON, XLSX, YAML, TSV), including integration with the Django admin panel.

## Use Cases
Django Fast TreeNode is suitable for a wide range of applications, from simple directories to complex systems with deep hierarchical structures:
- **Categories and taxonomies**: Manage product categories, tags, and classification systems.
- **Menus and navigation**: Create tree-like menus and nested navigation structures.
- **Forums and comments**: Store threaded discussions and nested comment chains.
- **Geographical data**: Represent administrative divisions, regions, and areas of influence.
- **Organizational and Business Structures**: Model company hierarchies, business processes, employees and departments.

In all applications, `django-fast-treenode` models show excellent performance and stability.

## Quick start
1. Run `pip install django-fast-treenode`.
2. Add `treenode` to `settings.INSTALLED_APPS`.

```python
INSTALLED_APPS = [
    ...
    'treenode',
]
```

3. Define your model inherit from `treenode.models.TreeNodeModel`.

```python
from treenode.models import TreeNodeModel

class Category(TreeNodeModel):
    name = models.CharField(max_length=255)
    treenode_display_field = "name"
```

4. Make your model-admin inherit from `treenode.admin.TreeNodeModelAdmin`.

```python
from treenode.admin import TreeNodeModelAdmin
from .models import Category

@admin.register(Category)
class CategoryAdmin(TreeNodeModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
```
5. Run migrations.

```bash 
python manage.py makemigrations
python manage.py migrate
```

6. Run server and use!

```bash
>>> root = Category.objects.create(name="Root")
>>> child = Category.objects.create(name="Child")
>>> child.set_parent(root)
>>> root_descendants_list = root.get_descendants()
>>> root_children_queryset = root.get_children_queryset()
>>> ancestors_pks = child.get_ancestors_pks()
```

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

Special thanks to [Fabio Caccamo](https://github.com/fabiocaccamo) for the idea behind creating a fast Django application for handling hierarchies and [Mathieu Leplatre](https://github.com/leplatrem) for the advice used in writing this application.

[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-fast-treenode/)
