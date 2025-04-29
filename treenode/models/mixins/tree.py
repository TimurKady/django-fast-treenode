# -*- coding: utf-8 -*-
"""
TreeNode Tree Mixin

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import json
import inspect
from django.db import models, transaction, connection
from collections import OrderedDict
from django.core.serializers.json import DjangoJSONEncoder

from ...cache import treenode_cache as cache


class TreeNodeTreeMixin(models.Model):
    """TreeNode Tree Mixin."""

    class Meta:
        """Moxin Meta Class."""

        abstract = True

    def clone_subtree(self, parent=None):
        """
        Clone self and entire subtree under given parent.

        Returns new root of the cloned subtree.
        """
        model = self._meta.model

        def _clone_node(node, parent):
            # Copy all regular fields (including ForeignKey via attname)
            data = {
                f.attname: getattr(node, f.attname)
                for f in node._meta.concrete_fields
                if not f.primary_key and f.name != "_path"
            }
            data['parent'] = parent

            # Create a new node
            new_node = model.objects.create(**data)

            # Copy ManyToMany fields
            for m2m_field in node._meta.many_to_many:
                related_ids = getattr(
                    node, m2m_field.name).values_list('pk', flat=True)
                getattr(new_node, m2m_field.name).set(related_ids)

            # Clone descendants recursively
            for child in node.get_children():
                _clone_node(child, new_node)

            return new_node

        return _clone_node(self, parent)

    @classmethod
    def get_tree(cls, instance=None):
        """
        Return an n-dimensional dictionary representing the model tree.

        If instance is passed, returns a subtree rooted at instance (using
        get_descendants_queryset), if not passed, builds a tree for all nodes
        (loads all records in one query).
        """
        # If instance is passed, we get all its descendants (including itself)
        if instance:
            queryset = instance.get_descendants_queryset(include_self=True)
        else:
            # Load all records at once
            queryset = cls.objects.get_queryset()

        # Dictionary for quick access to nodes by id and list for iteration
        nodes_by_id = {}
        nodes_list = []

        # Loop through all nodes using an iterator
        for node in queryset.order_by("_path").iterator(chunk_size=1000):
            # Create a dictionary for the node.
            node_dict = OrderedDict()
            node_dict['id'] = node.id
            node_dict['parent'] = node.parent_id
            node_dict['priority'] = node.priority
            node_dict['depth'] = node.get_depth()
            node_dict['path'] = node.get_order()
            node_dict['children'] = []  # node.get_children_pks()

            # Add the rest of the model fields.
            # Iterate over all the fields obtained via _meta.get_fields()
            fields = [
                f for f in node._meta.get_fields()
                if f.concrete and not f.auto_created and
                not f.name.startswith('_')
            ]

            for field in fields:
                # Skipping fields that are already added or not required
                # (e.g. tn_closure or virtual links)
                if field.name in [
                        'id', 'parent', 'priority', '_depth', 'children']:
                    continue

                try:
                    value = getattr(node, field.name)
                except Exception:
                    value = None

                # If the field is many-to-many, we get a list of IDs of
                # related objects
                if hasattr(value, 'all'):
                    value = list(value.all().values_list('id', flat=True))

                node_dict[field.name] = value

            # Save the node both in the list and in the dictionary by id
            # for quick access
            nodes_by_id[node.id] = node_dict
            nodes_list.append(node_dict)

        # Build a tree: assign each node a list of its children
        tree = []
        for node_dict in nodes_list:
            parent_id = node_dict['parent']
            # If there is a parent and it is present in nodes_by_id, then
            # add the current node to the list of its children
            if parent_id and parent_id in nodes_by_id:
                parent_node = nodes_by_id[parent_id]
                parent_node['children'].append(node_dict)
            else:
                # If there is no parent, this is the root node of the tree
                tree.append(node_dict)

        return tree

    @classmethod
    def get_tree_json(cls, instance=None):
        """Represent the tree as a JSON-compatible string."""
        tree = cls.get_tree(instance)
        return DjangoJSONEncoder().encode(tree)

    @classmethod
    def load_tree(cls, tree_data):
        """
        Load a tree from a list of dictionaries.

        - Ignores visual/path metadata ('path', 'depth', '_path', '_depth')
        - Accepts 'id', 'name', 'priority', 'parent'
        - Automatically recalculates _path, _depth, priority after loading
        """
        # Step 1: Flatten nested tree into list of nodes with temporary
        # parent references
        def flatten_tree(tree, parent_temp_id=None):
            flat = []
            for node in tree:
                node = node.copy()
                children = node.pop('children', [])
                node_id = node.pop('id', None)
                node.pop('path', None)
                node.pop('depth', None)
                node.pop('parent', None)
                flat_node = {
                    **node,
                    '_id': int(node_id) if node_id is not None else None,
                    '_parent': int(parent_temp_id) if parent_temp_id is not None else None  # noqa: D501
                }
                flat.append(flat_node)
                flat.extend(flatten_tree(children, parent_temp_id=node_id))
            return flat

        raw_data = flatten_tree(tree_data)

        # Step 2: Identify which objects should be updated
        pks = [r["_id"] for r in raw_data if r["_id"] is not None]
        existing_ids = set(cls.objects.filter(
            pk__in=pks).values_list('id', flat=True))
        to_update_ids = {r["_id"] for r in raw_data if r["_id"] in existing_ids}

        existing_objs = {
            obj.pk: obj for obj in cls.objects.filter(pk__in=to_update_ids)}

        # Step 3: Determine tree levels for correct creation order
        levels = {}
        for record in raw_data:
            level = 0
            p = record.get('_parent')
            while p:
                level += 1
                p = next((r['_parent']
                         for r in raw_data if r['_id'] == p), None)
            levels.setdefault(level, []).append(record)

        records_by_level = [
            sorted(levels[level], key=lambda x: x.get('_parent') or -1)
            for level in sorted(levels)
        ]

        # Step 4: Map old temporary IDs to actual DB IDs
        created_objects = []
        updated_objects = []
        # ID mapping for existing objects
        id_map = {pk: pk for pk in to_update_ids}

        model_fields = {
            f.name for f in cls._meta.get_fields()
            if f.concrete and not f.auto_created and not f.name.startswith('_')
        }

        # Step 5: Process records level by level
        for level_records in records_by_level:
            objs_to_create = []
            objs_to_update = []
            fields_to_update_set = set()

            for record in level_records:
                temp_id = record['_id']
                temp_parent = record.get('_parent')
                data = {k: v for k, v in record.items() if not k.startswith(
                    '_') and k in model_fields}

                if temp_parent and temp_parent in id_map:
                    data['parent_id'] = id_map[temp_parent]

                if temp_id in to_update_ids:
                    obj = existing_objs[temp_id]
                    for field, value in data.items():
                        setattr(obj, field, value)
                    setattr(obj, '_temp_parent', temp_parent)
                    objs_to_update.append(obj)
                    fields_to_update_set.update(data.keys())
                else:
                    obj = cls(**data)
                    obj.full_clean()
                    setattr(obj, '_temp_id', temp_id)
                    setattr(obj, '_temp_parent', temp_parent)
                    objs_to_create.append(obj)

            # Step 6: Bulk create and track real IDs
            if objs_to_create:
                created = cls.objects.bulk_create(objs_to_create)
                for obj in created:
                    temp_id = getattr(obj, '_temp_id')
                    id_map[temp_id] = obj.id
                    delattr(obj, '_temp_id')
                    created_objects.append(obj)

            # Step 7: Bulk update existing objects
            if objs_to_update:
                for obj in objs_to_update:
                    obj.full_clean()
                cls.objects.bulk_update(
                    objs_to_update, list(fields_to_update_set))
                updated_objects.extend(objs_to_update)

        all_objects = created_objects + updated_objects

        # Step 8: Finalize parent assignments using ID map
        for obj in all_objects:
            temp_parent = getattr(obj, '_temp_parent', None)
            if temp_parent is not None and temp_parent in id_map:
                obj.parent_id = id_map[temp_parent]
            for attr in ['_temp_id', '_temp_parent']:
                if hasattr(obj, attr):
                    delattr(obj, attr)

        cls.objects.bulk_update(all_objects, ['parent_id'])

        # Step 9: Rebuild tree structure (path, depth, priority)
        cls.tasks.run()

        # Step 10: Invalidate tree-related caches
        cache.invalidate(cls._meta.label)

    @classmethod
    def load_tree_json(cls, json_str):
        """
        Decode a JSON string into a dictionary.

        Takes a JSON-compatible string and decodes it into a tree structure.
        """
        try:
            tree_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")
        return tree_data

    @classmethod
    def get_tree_annotated(cls):
        """
        Get an annotated list from a tree branch.

        Something like this will be returned:
        [
            (a,     {'open':True,  'close':[],    'level': 0})
            (ab,    {'open':True,  'close':[],    'level': 1})
            (aba,   {'open':True,  'close':[],    'level': 2})
            (abb,   {'open':False, 'close':[],    'level': 2})
            (abc,   {'open':False, 'close':[0,1], 'level': 2})
            (ac,    {'open':False, 'close':[0],   'level': 1})
        ]

        All nodes are ordered by materialized path.
        This can be used with a template like this:

        {% for item, info in annotated_list %}
            {% if info.open %}
                <ul><li>
            {% else %}
                </li><li>
            {% endif %}

            {{ item }}

            {% for close in info.close %}
                </li></ul>
            {% endfor %}
        {% endfor %}

        """
        # Load the tree with the required preloads and depth annotation.
        queryset = cls.objects.all()
        # Convert queryset to list for indexed access
        nodes = list(queryset)
        total_nodes = len(nodes)
        sorted_nodes = cls._sort_node_list(nodes)

        result = []

        for i, node in enumerate(sorted_nodes):
            # Get the value to display the node
            value = str(node)
            # Determine if there are descendants (use prefetch_related to avoid
            # additional queries)
            value_open = len(node.children.all()) > 0
            level = node.depth

            # Calculate the "close" field
            if i + 1 < total_nodes:
                next_node = nodes[i + 1]
                depth_diff = level - next_node.depth
                # If the next node is at a lower level, then some open
                # levels need to be closed
                value_close = list(range(next_node.depth, level)
                                   ) if depth_diff > 0 else []
            else:
                # For the last node, close all open levels
                value_close = list(range(0, level + 1))

            result.append(
                (value, {
                    "open": value_open,
                    "close": value_close,
                    "level": level
                })
            )
        return result

    @classmethod
    def update_tree(cls):
        """Rebuld the tree."""
        cls.tasks.add("update", None)
        cls.tasks.run()

    def delete_tree(self, include_self=True):
        """
        Delete current node and all descendants.

        If include_self=False, only descendants will be deleted.
        """
        table = self._meta.db_table
        path = self._path
        like_pattern = f"{path}.%"

        if include_self:
            sql = f"""
                DELETE FROM {table}
                WHERE _path = %s OR _path LIKE %s
            """
            params = [path, like_pattern]
        else:
            sql = f"""
                DELETE FROM {table}
                WHERE _path LIKE %s
            """
            params = [like_pattern]

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
        self.clear_cache()

    @classmethod
    def delete_forest(cls):
        """Delete the whole tree for the current node class."""
        # cls.objects.all()._raw_delete(cls._base_manager.db)
        table = cls._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table}")
        cache.invalidate(cls._meta.label)

# The end
