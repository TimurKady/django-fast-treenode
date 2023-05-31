# -*- coding: utf-8 -*-
"""
TreeNode Models Module

"""


from django.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from six import with_metaclass
from . import classproperty
from .compat import force_str
from .factory import TreeFactory
from .managers import TreeNodeManager


class TreeNodeModel(with_metaclass(TreeFactory, models.Model)):

    treenode_display_field = None

    tn_parent = models.ForeignKey(
        'self',
        related_name='tn_children',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Parent'),
    )

    tn_priority = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Priority'),
    )

    objects = TreeNodeManager()

    class Meta:
        abstract = True

    def __str__(self):
        if self.treenode_display_field:
            return str(getattr(self, self.treenode_display_field))
        else:
            return 'Node %d' % str(self.pk)

    # Public methods

    @classmethod
    def get_roots(cls):
        """Get a list with all root nodes"""
        return list(item for item in cls.objects.filter(tn_parent=None))

    @classmethod
    def get_roots_queryset(cls):
        """Get root nodes queryset"""
        return cls.objects.filter(tn_parent=None)

    @classmethod
    def get_ordered_queryset(cls):
        """Returns a set of nodes sorted by tn_priority"""

        qs = cls.objects.all()
        table = cls._meta.db_table
        pk_list = sorted([node.pk for node in qs], key=lambda x: x.tn_order)
        clauses = ' '.join(
            ['WHEN %s.id=%s THEN %s' % (table, pk, i)
             for i, pk in enumerate(pk_list)]
        )
        order = 'CASE %s END' % clauses
        queryset = cls.objects.filter(pk__in=pk_list).extra(
            select={'ordering': order}, order_by=('ordering',))
        return queryset

    @classmethod
    def get_tree(cls, instance=None):
        """Get a n-dimensional dict representing the model tree"""

        objs_list = list(instance,) if instance else cls.get_roots()
        objs_tree = list()
        for item in objs_list:
            objs_tree.append(item.object2dict(item, []))
        return objs_tree

    @classmethod
    def get_tree_display(cls, cache=True):
        """Get a multiline string representing the model tree"""

        objs = list(cls.objects.all())
        return '\n'.join(['%s' % (obj,) for obj in objs])

    @classmethod
    def update_tree(cls):
        """Update tree manually, useful after bulk updates"""

        cls.closure_model.objects.all().delete()

        # Apparently later, you should think about using iterators to reduce
        # the amount of memory used.
        # I'm sorry, I don't have time for that right now.

        cls.closure_model.objects.bulk_create([
            cls.closure_model(
                parent_id=item.pk,
                child_id=item.pk,
                depth=0
            )
            for item in cls.objects.all()
        ])

        for node in cls.objects.all():
            queryset = cls.closure_model.objects.all()
            parents = queryset.filter(
                child=node.parent).values('parent', 'depth')
            children = queryset.filter(
                parent=node).values('child', 'depth')
            objects = [
                cls.closure_model(
                    parent_id=p['parent'],
                    child_id=c['child'],
                    depth=p['depth'] + c['depth'] + 1
                )
                for p in parents
                for c in children
            ]
            cls.closure_model.objects.bulk_create(objects)
        cls._update_orders()

    @classmethod
    def delete_tree(cls):
        """Delete the whole tree for the current node class"""

        cls.closure_model.objects.all().delete()
        cls.objects.all().delete()

    def get_ancestors(self, include_self=True, depth=None):
        """Get a list with all ancestors (ordered from root to self/parent)"""

        options = dict(child_id=self.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})

        qs = self._closure_model.objects.filter(**options).order_by('-depth')

        return list(item.parent for item in qs)

    def get_ancestors_count(self, include_self=True, depth=None):
        """Get the ancestors count"""

        return self.get_ancestors_queryset(include_self, depth).count()

    def get_ancestors_pks(self, include_self=True, depth=None):
        """Get the ancestors pks list"""

        options = dict(child_id=self.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})

        qs = self._closure_model.objects.filter(**options).order_by('-depth')

        return list(item.parent.pk for item in qs)

    def get_ancestors_queryset(self, include_self=True, depth=None):
        """Get the ancestors queryset (self, ordered from parent to root)"""

        options = dict(child_id=self.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})

        qs = self._closure_model.objects.filter(**options).order_by('-depth')
        select = list(item.parent.pk for item in qs)
        resurt = self._meta.model.objects.filter(pk__in=select)
        return resurt

    def get_breadcrumbs(self, attr=None):
        """Get the breadcrumbs to current node (self, included)"""

        qs = self._closure_model.objects.filter(child=self).order_by('-depth')
        if attr:
            return list(getattr(item.parent, attr) for item in qs)
        else:
            return list(item.parent for item in qs)

    def get_children(self):
        """Get a list containing all children"""

        return list(self.tn_children.all())

    def get_children_count(self):
        """Get the children count"""

        return self.get_children_queryset().count()

    def get_children_pks(self):
        """Get the children pks list"""

        return [ch.pk for ch in self.tn_children.all()]

    def get_children_queryset(self):
        """Get the children queryset"""
        return self.tn_children.all()

    def get_depth(self):
        """Get the node depth (self, how many levels of descendants)"""

        depths = self._closure_model.objects.filter(parent=self).values_list(
            'depth',
            flat=True
        )
        return max(depths)

    def get_descendants(self, include_self=False, depth=None):
        """Get a list containing all descendants"""
        return list(self.get_descendants_queryset(include_self, depth))

    def get_descendants_count(self, include_self=False, depth=None):
        """Get the descendants count"""
        return self.get_descendants_queryset().count()

    def get_descendants_pks(self, include_self=False, depth=None):
        """Get the descendants pks list"""
        options = dict(parent_id=self.pk, depth__gte=0 if include_self else 1)
        if depth:
            options.update({'depth__lte': depth})

        qs = self._closure_model.objects.filter(**options)
        return [ch.child.pk for ch in qs] if qs else []

    def get_descendants_queryset(self, include_self=False, depth=None):
        """Get the descendants queryset"""

        pks = self.get_descendants_pks(include_self, depth)
        return self._meta.model.objects.filter(**pks)

    def get_descendants_tree(self):
        """Get a n-dimensional dict representing the model tree"""

        return self._meta.model.get_tree(instance=self)

    def get_descendants_tree_display(self, include_self=False, depth=None):
        """Get a multiline string representing the model tree"""

        objs = self.get_descendants()
        return '\n'.join(['%s' % (obj,) for obj in objs])

    def get_first_child(self):
        """Get the first child node"""
        return self.get_children_queryset().first()

    def get_index(self):
        """Get the node index (self, index in node.parent.children list)"""
        source = self.get_siblings()
        return source.index(self)

    def get_last_child(self):
        """Get the last child node"""
        return self.get_children_queryset().last()

    def get_level(self):
        """Get the node level (self, starting from 1)"""

        levels = self._closure_model.objects.filter(child=self).values_list(
            'depth',
            flat=True
        )
        return max(levels) + 1

    def get_path(self, prefix='', suffix='', delimiter='.', format_str=''):
        """Return Materialized Path of node"""

        str_ = '{%s}' % format_str
        return prefix + delimiter.join(
            str_.format(i) for i in self.get_breadcrumbs(attr='tn_priority')
        ) + suffix

    def get_parent(self):
        """Get the parent node"""
        return self.tn_parent

    def get_parent_pk(self):
        """Get the parent node pk"""
        return self.tn_parent.pk if self.tn_parent else None

    def set_parent(self, parent_obj):
        """Set the parent node"""
        self.tn_parent = parent_obj

    def get_priority(self):
        return self.tn_priority

    def set_priority(self, priority=0):
        """Set the node priority"""
        self.tn_priority = priority

    def get_root(self):
        """Get the root node for the current node"""
        qs = self._closure_model.objects.filter(child=self).order_by('depth')
        return qs.last().parent if qs.count() > 0 else None

    def get_root_pk(self):
        """Get the root node pk for the current node"""
        self.get_root().pk

    def get_siblings(self):
        """Get a list with all the siblings"""
        return list(self.get_siblings_queryset())

    def get_siblings_count(self):
        """Get the siblings count"""
        return self.get_siblings_queryset().count()

    def get_siblings_pks(self):
        """Get the siblings pks list"""
        return [item.pk for item in self.get_siblings_queryset()]

    def get_siblings_queryset(self):
        """Get the siblings queryset"""
        if self.tn_parent:
            queryset = self.tn_parent.tn_children.all()
        else:
            queryset = self._meta.model.objects.filter(tn_parent__isnull=True)
        return queryset.exclude(pk=self.pk)

    def is_ancestor_of(self, target_obj):
        """Return True if the current node is ancestor of target_obj"""
        return self.pk in target_obj.get_ancestors_pks()

    def is_child_of(self, target_obj):
        """Return True if the current node is child of target_obj"""

        return self.pk in target_obj.get_children_pks()

    def is_descendant_of(self, target_obj):
        """Return True if the current node is descendant of target_obj"""
        return self.pk in target_obj.get_descendants_pks()

    def is_first_child(self):
        """Return True if the current node is the first child"""
        return self.tn_priority == 0

    def is_last_child(self):
        """Return True if the current node is the last child"""

        return self.tn_priority == self.get_siblings_count() - 1

    def is_leaf(self):
        """Return True if the current node is leaf (self, it has not children)"""
        return self.tn_children.count() == 0

    def is_parent_of(self, target_obj):
        """Return True if the current node is parent of target_obj"""
        return self == target_obj.tn_parent

    def is_root(self):
        """Return True if the current node is root"""
        return self.tn_parent is None

    def is_root_of(self, target_obj):
        """Return True if the current node is root of target_obj"""
        return self == target_obj.get_root()

    def is_sibling_of(self, target_obj):
        """Return True if the current node is sibling of target_obj"""
        return self in target_obj.tn_parent.tn_children.all()

    # I think this method is not needed.
    # Clearing entries in the Closure Table will happen automatically
    # via cascading deletion

    # def delete(self, cascade=True, *args, **kwargs):
    #    """Delete a node if cascade=True (default behaviour), children and
    #    descendants will be deleted too, otherwise children's parent will be
    #    set to None (then children become roots)"""

    # pass

    # Public properties
    # All properties map a get_{{property}}() method.

    @property
    def ancestors(self):
        return self.get_ancestors()

    @property
    def ancestors_count(self):
        return self.get_ancestors_count()

    @property
    def ancestors_pks(self):
        return self.get_ancestors_pks()

    @property
    def breadcrumbs(self):
        return self.get_breadcrumbs()

    @property
    def children(self):
        return self.get_children()

    @property
    def children_count(self):
        return self.get_children_count()

    @property
    def children_pks(self):
        return self.get_children_pks()

    @property
    def depth(self):
        return self.get_depth()

    @property
    def descendants(self):
        return self.get_descendants()

    @property
    def descendants_count(self):
        return self.get_descendants_count()

    @property
    def descendants_pks(self):
        return self.get_descendants_pks()

    @property
    def descendants_tree(self):
        return self.get_descendants_tree()

    @property
    def descendants_tree_display(self):
        return self.get_descendants_tree_display()

    @property
    def first_child(self):
        return self.get_first_child()

    @property
    def index(self):
        return self.get_index()

    @property
    def last_child(self):
        return self.get_last_child()

    @property
    def level(self):
        return self.get_level()

    @property
    def parent(self):
        return self.tn_parent

    @property
    def parent_pk(self):
        return self.get_parent_pk()

    @property
    def priority(self):
        return self.get_priority()

    @classproperty
    def roots(cls):
        return cls.get_roots()

    @property
    def root(self):
        return self.get_root()

    @property
    def root_pk(self):
        return self.get_root_pk()

    @property
    def siblings(self):
        return self.get_siblings()

    @property
    def siblings_count(self):
        return self.get_siblings_count()

    @property
    def siblings_pks(self):
        return self.get_siblings_pks()

    @classproperty
    def tree(cls):
        return cls.get_tree()

    @classproperty
    def tree_display(cls):
        return cls.get_tree_display()

    # ----------------------------------------------------------------------
    # Private methods
    # The usage of these methods is only allowed by developers. In future
    # versions, these methods may be changed or removed without any warning.

    @property
    def _closure_model(self):
        return self._meta.model.closure_model

    @property
    def tn_order(self):
        path = self.get_breadcrumbs(attr='tn_priority')
        return '.'.join(['{:0>6g}'.format(i) for i in path])

    def object2dict(self, instance, exclude=[]):
        """Convert Class Object to python dict"""

        result = dict()

        if not hasattr(instance, '__dict__'):
            return instance

        new_subdic = dict(vars(instance))
        for key, value in new_subdic.items():
            if key.startswith('_') or key in exclude:
                continue
            result.update({key: self.object2dict(value, exclude)})

        childs = instance.tn_children.all()
        if childs.count() > 0:
            result.update({
                'children': [
                    obj.object2dict(obj, exclude)
                    for obj in childs.all()]
            })
        result.update({'path': instance.get_path(format_str=':d')})
        return result

    def get_display(self, indent=True, mark='— '):
        indentation = (mark * self.tn_ancestors_count) if indent else ''
        indentation = force_str(indentation)
        text = self.get_display_text()
        text = force_str(text)
        return indentation + text

    def get_display_text(self):
        """
        Gets the text that will be indented in `get_display` method.
        Returns the `treenode_display_field` value if specified,
        otherwise falls back on the model's pk.
        Override this method to return another field or a computed value. #27
        """
        text = ''
        if (hasattr(self, 'treenode_display_field') and
                self.treenode_display_field is not None):
            field_name = getattr(self, 'treenode_display_field')
            text = getattr(self, field_name, '')
        if not text and self.pk:
            text = self.pk
        return force_str(text)

    @transaction.atomic
    def _insert(self):
        """Adds a new entry to the Adjacency Table and the Closure Table"""

        instance = self._closure_model.objects.create(
            parent=self,
            child=self,
            depth=0
        )
        instance.save()

        qs = self._closure_model.objects.all()
        parents = qs.filter(child=self.tn_parent).values('parent', 'depth')
        children = qs.filter(parent=self).values('child', 'depth')
        objects = [
            self._closure_model(
                parent_id=p['parent'],
                child_id=c['child'],
                depth=p['depth'] + c['depth'] + 1
            )
            for p in parents
            for c in children
        ]
        self._closure_model.objects.bulk_create(objects)

    @transaction.atomic
    def _move_to(self, old_parent):
        target = self.tn_parent
        qs = self._closure_model.objects.all()
        subtree = qs.filter(parent=self).values('child', 'depth')
        supertree = qs.filter(child=target).values('parent', 'depth')

        # Step 1. Delete
        subtree_pks = [node.child.pk for node in qs.filter(parent=self)]
        qs.filter(child_id__in=subtree_pks).exclude(
            parent_id__in=subtree_pks).delete()

        # Step 2. Insert
        objects = [
            self._closure_model(
                parent_id=p['parent'],
                child_id=c['child'],
                depth=p['depth'] + c['depth'] + 1
            )
            for p in supertree
            for c in subtree
        ]
        self._closure_model.objects.bulk_create(objects)

    def _order(self):

        queryset = self.get_siblings_queryset()

        if self.tn_priority > queryset.count():
            self.tn_priority = queryset.count()

        siblings = list(node for node in queryset)
        sorted_siblings = sorted(siblings, key=lambda x: x.tn_priority)
        sorted_siblings.insert(self.tn_priority, self)

        for index in range(len(sorted_siblings)):
            sorted_siblings[index].tn_priority = index

        self._meta.model.objects.bulk_update(
            sorted_siblings, ('tn_priority', ))

    def save(self, force_insert=False, *args, **kwargs):

        try:
            old = self._meta.model.objects.get(pk=self.pk)
            old_parent = old.tn_parent
        except:
            force_insert = True

        super().save(*args, **kwargs)
        self._order()

        if force_insert:
            self._insert()
        elif old_parent != self.tn_parent:
            self._move_to(old_parent)

    # The end
