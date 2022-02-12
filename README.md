# New Django-Treenode 
__Combination of Adjacency List and Closure Table__


## Debut idea
This is a modification of the reusable [django-treenode](https://github.com/fabiocaccamo/django-treenode) application developed by [Fabio Caccamo](https://github.com/fabiocaccamo).
The original application has significant advantages over other analogues, and indeed, is one of the best implementations of support for hierarchical structures for Django. 

Fabio's idea was to use the Adjacency List method to store the data tree. The most probable and time-consuming requests are calculated in advance and stored in the database. Also, most requests are cached. As a result, query processing is carried out in one call to the database or without it at all.

However, this application has a number of undeniable shortcomings:
* the selected pre-calculations scheme entails high costs for adding a new element;
* inserting new elements uses signals, which leads to failures when using bulk-operations;
* the problem of ordering elements by priority inside the parent node has not been resolved.

My idea was to solve these problems by combining the adjacency list with the Closure Table. Main advantages:
* the Closure Model is generated automatically;
* maintained compatibility with the original package at the level of documented functions;
* most requests are satisfied in one call to the database;
* inserting a new element takes two calls to the database without sinals usage;
* bulk-operations are supported;
* the cost of creating a new dependency is reduced many times;
* useful functionality added for some methods (e.g.  the `include_self=False` and `depth` parameters has been added to functions that return lists/querysets);
* additionally, the package includes a tree view widget for the `tn_parent` field in the change form.

Of course, at large levels of nesting, the use of the Closure Table leads to an increase in resource costs. But at the same time, the combined scheme still generally outperforms the original application in terms of performance.

## Theory
You can get a basic understanding of what is a Closure Table from:
* [presentation](https://www.slideshare.net/billkarwin/models-for-hierarchical-data) by Bill Karwin;
* [article](https://dirtsimple.org/2010/11/simplest-way-to-do-tree-based-queries.html) by blogger Dirt Simple;
* [article](https://towardsdatascience.com/closure-table-pattern-to-model-hierarchies-in-nosql-c1be6a87e05b) by Andriy Zabavskyy.

You can easily find additional information on your own on the Internet.

## Interface changes
The following methods have been added or changed:

### update_tree()
```
cls.update_tree()
```
Now you should call this function only when absolutely necessary. For example, if during a bulk update you affect the values of the `tn_parent` field. Otherwise, there is no need to use it.

When updating an existing project, simply call this function once. It will automatically build a new and complete Closure Table for your tree.

### ancestors & descendants
```
self.get_ancestors(include_self=True, depth=None)
self.get_ancestors_count(include_self=True, depth=None)
self.get_ancestors_pks(include_self=True, depth=None)
self.get_ancestors_queryset(include_self=True, depth=None)
self.get_descendants(include_self=False, depth=None)
self.get_descendants_count(include_self=False, depth=None)
self.get_descendants_pks(include_self=False, depth=None)
self.get_descendants_queryset(include_self=False, depth=None)
self.get_descendants_tree_display(include_self=False, depth=None)
```
These functions now take two extra arguments each insert `include_self` and `depth`. Default values allow these methods to be called in the old style.

### get_tree()
```
cls.get_tree(instance=None)
```
Returns an n-dimensional dictionary representing the model tree. Each node contains a `"children"=[]` key with a list of nested dictionaries of child nodes.

### get_ordered_queryset()
```
cls.get_ordered_queryset()
```
Returns a queryset of nodes ordered by `tn_priority` each node. For example:
- N.1
- N.1.1
- N.1.1.1
- N.1.1.2
- N.2
- N.2.1
- ...

This method uses a lot of memory, `RawSQL()` and `.extra()` QuerySet method. It's possible I'll change this method due to concerns about [aiming to deprecate](https://docs.djangoproject.com/en/4.0/ref/models/querysets/#extra) `.extra()` method from Django in the future. Use it only if you cannot otherwise assemble an ordered tree from an Adjacency Table and a Closure Table. In most cases, the data in one Adjacency Table is sufficient for such an assembly. You can easily find the corresponding algorithms (two-pass and one-pass) on the Internet.

### get_path()
```
self.get_path(prefix='', suffix='', delimiter='.', format_str='')
```
Added the function of decorating a materialized path. The path is formed according to the value of the `tn_priority` field.

### Access to Closure Table
```
cls.closure_model
self._closure_model
```
These two attributes give you access to your model's Closure Table

## Cautions
The code provided is intended for testing by developers and is not recommended for use in production projects. Only general tests were carried out. The risk of using the code lies entirely with you.

Don't access treenode fields directly! Most of them have been removed as unnecessary. Use functions documented in the [source application](https://github.com/fabiocaccamo/django-treenode).

## Dependencies
The code provided is not a reusable application. To use, run `pip install six`

## Plans for the future and prospects
Future plans:
* catch bugs and finish full testing;
* may be will restore caching;
* may be will add the ability to determine the priority of the parent by any field, for example, by creation date or alphabetical order;
* to perform final code optimization;
* issue in the form of a reusable application;
* to be happy, to don't worry, until die.

Your wishes, objections, comments are welcome.
