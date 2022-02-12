# New Treenode: combination of Adjacency List and Closure Table
## Debut idea
This is a modification of the reusable [django-treenode](https://github.com/fabiocaccamo/django-treenode) application developed by [Fabio Caccamo](https://github.com/fabiocaccamo).
The original application has significant advantages over other analogues, and indeed, is one of the best implementations of support for hierarchical structures for Django. 

Fabio's idea was to use the Adjacency List method to store the data tree. The most probable and time-consuming requests are calculated in advance and stored in the database. Also, most requests are cached after the request. As a result, query processing is carried out in one call to the database or without it at all.

However, this application has a number of undeniable shortcomings:
* the selected pre-calculations scheme entails high costs for adding a new element;
* inserting new elements uses signals, which leads to failures when using bulk-operations;
* the problem of ordering elements by priority inside the parent node has not been resolved.

My idea was to solve these problems by combining the adjacency list with the Closure Table. Main advantages:
* the Closure Model is generated automatically;
* maintained compatibility with the original package at the level of documented functions;
* most requests are satisfied in one image to the database;
* inserting a new element takes two images to the database;
* bulk-operations are supported;
* the cost of creating a new dependency is reduced many times;
* useful functionality added for some methods (e.g.  the include_self=False and depth parameters has been added to functions that return lists/query sets);
* additionally, the package includes a tree view widget for the `tn_parent` field in the change form.

Of course, at large levels of nesting, the use of the Closure Table leads to an increase in resource costs. But at the same time, the combined scheme still generally outperforms the original application in terms of performance.

## Theory
You can get a basic understanding of what is a Closure Table from:
* [presentation](https://www.slideshare.net/billkarwin/models-for-hierarchical-data) by Bill Karwin;
* [article](https://dirtsimple.org/2010/11/simplest-way-to-do-tree-based-queries.html) by blogger Dirt Simple;
* [article](https://towardsdatascience.com/closure-table-pattern-to-model-hierarchies-in-nosql-c1be6a87e05b) by Andriy Zabavskyy.

You can easily find additional information on your own on the Internet.

## Interface changes
```
cls.update_tree()
```
Now you should call this function only when absolutely necessary. For example, if during a bulk update you affect the values of the `tn_parent` field. Otherwise, there is no need to use it.

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
These functions now take two extra arguments each insert include_self=False, depth=None. Default values allow these methods to be called in the old style.

```
self.get_path(prefix='', suffix='', delimiter='.', format_str='')
```
Added the function of decorating a materialized path. The path is formed according to the value of the `tn_priority` field.

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
* restore caching;
* add the ability to determine the priority of the parent by any field, for example, by creation date or alphabetical order;
* finish testing;
* issue in the form of a reusable application;
* add search functionality;
* perform final code optimization;
* live happily until death.

Your wishes, objections, comments are welcome.
