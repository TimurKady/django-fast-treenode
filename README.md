# Treenode with closure table
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
* useful functionality added for some methods (see source code);
* additionally, the package includes a tree view widget for the `tn_parent` field in the change form.

Of course, at large levels of nesting, the use of the Closing Table leads to an increase in resource costs. But at the same time, the combined scheme still generally outperforms the original application in terms of performance.

## Cautions
The code provided is intended for testing by developers and is not recommended for use in production projects. Only general tests were carried out. The risk of using the code lies entirely with you.

## Dependencies
The code provided is not a reusable application. To use, run `pip install six`

## Prospects
Future plans:
* restore caching;
* add the ability to determine the priority of the parent by any field, for example, by creation date or alphabetical order;
* finish testing;
* issue in the form of a reusable application;
* add search functionality;
* perform final code optimization.

Wishes are welcome.
