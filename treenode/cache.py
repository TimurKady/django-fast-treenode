# -*- coding: utf-8 -*-
"""
TreeNode Cache Module

This module provides a singleton-based caching system for TreeNode models.
It includes optimized key generation, cache size tracking,
and an eviction mechanism to ensure efficient memory usage.

Features:
- Singleton cache instance to prevent redundant allocations.
- Custom cache key generation using function parameters.
- Automatic cache eviction when memory limits are exceeded.
- Decorator `@cached_method` for caching method results.

Version: 2.2.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import hashlib
import msgpack
import sys
import threading
from collections import deque, defaultdict, OrderedDict
from django.conf import settings
from django.core.cache import caches
from functools import lru_cache
from functools import wraps


# ---------------------------------------------------
# Utilities
# ---------------------------------------------------

_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_CLEARINT_THESHOLD = 0.8
_EVICT_INTERVAL = 50


@lru_cache(maxsize=1000)
def to_base36(num):
    """
    Convert an integer to a base36 string.

    For example: 10 -> 'A', 35 -> 'Z', 36 -> '10', etc.
    """
    if num == 0:
        return '0'
    sign = '-' if num < 0 else ''
    num = abs(num)
    result = []
    while num:
        num, rem = divmod(num, 36)
        result.append(_DIGITS[rem])
    return sign + ''.join(reversed(result))


# ---------------------------------------------------
# Caching
# ---------------------------------------------------

class TreeCache:
    """Singleton class for managing the TreeNode cache."""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton new."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(TreeCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, cache_limit=100 * 1024 * 1024):
        """
        Initialize the cache.

        If the 'treenode' key is present in settings.CACHES, the corresponding
        backend is used.
        Otherwise, the custom dictionary is used.
        The cache size (in bytes) is taken from
        settings.TREENODE_CACHE_LIMIT (MB), by default 100 MB.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return

        # Get the cache limit (MB), then convert to bytes.
        cache_limit_mb = getattr(settings, 'TREENODE_CACHE_LIMIT', 100)
        self.cache_limit = cache_limit_mb * 1024 * 1024

        # Select backend: if there is 'treenode' in settings.CACHES, use it.
        # Otherwise, use our own dictionary.
        if hasattr(settings, 'CACHES') and 'treenode' in settings.CACHES:
            self.cache = caches['treenode']
        else:
            # We use our dictionary as a backend.
            self.cache = OrderedDict()

        self.order = deque()            # Queue for FIFO implementation.
        self.total_size = 0             # Current cache size in bytes.
        self.lock = threading.Lock()    # Lock for thread safety.

        # Additional index for fast search of keys by prefix
        # Format: {prefix: {key1, key2, ...}}
        self.prefix_index = defaultdict(set)
        # Dictionary to store the sizes of each key (key -> size in bytes)
        self.sizes = {}
        # Dictionary to store the prefix for each key to avoid repeated
        # splitting
        self.key_prefix = {}

        # Counter for number of set operations for periodic eviction
        self._set_counter = 0
        # Evict cache every _evict_interval set operations when using external
        # backend
        self._evict_interval = _EVICT_INTERVAL

        self._initialized = True

    def generate_cache_key(self, label, func_name, unique_id, *args, **kwargs):
        """
        Generate a cache key.

        <label>_<func_name>_<unique_id>_<hash>
        """
        # If using custom dict backend, use simple key generation without
        # serialization.
        if isinstance(self.cache, dict):
            sorted_kwargs = sorted(kwargs.items())
            return f"{label}_{func_name}_{unique_id}_{args}_{sorted_kwargs}"
        else:
            try:
                # Using msgpack for fast binary representation of arguments
                sorted_kwargs = sorted(kwargs.items())
                params_bytes = msgpack.packb(
                    (args, sorted_kwargs), use_bin_type=True)
            except Exception:
                params_bytes = repr((args, kwargs)).encode('utf-8')
            # Using MD5 for speed (no cryptographic strength)
            hash_value = hashlib.md5(params_bytes).hexdigest()
            return f"{label}_{func_name}_{unique_id}_{hash_value}"

    def get_obj_size(self, value):
        """
        Determine the size of the object in bytes.

        If the value is already in bytes or bytearray, simply returns its
        length. Otherwise, uses sys.getsizeof for an approximate estimate.
        """
        if isinstance(value, (bytes, bytearray)):
            return len(value)
        return sys.getsizeof(value)

    def set(self, key, value):
        """
        Store the value in the cache.

        Stores the value in the cache, updates the FIFO queue, prefix index,
        size dictionary, and total cache size.
        """
        # Idea 1: Store raw object if using custom dict backend, otherwise
        # serialize using msgpack.
        if isinstance(self.cache, dict):
            stored_value = value
        else:
            try:
                stored_value = msgpack.packb(value, use_bin_type=True)
            except Exception:
                stored_value = value

        # Calculate the size of the stored value
        if isinstance(stored_value, (bytes, bytearray)):
            size = len(stored_value)
        else:
            size = sys.getsizeof(stored_value)

        # Store the value in the cache backend
        if isinstance(self.cache, dict):
            self.cache[key] = stored_value
        else:
            self.cache.set(key, stored_value)

        # Update internal structures under lock
        with self.lock:
            if key in self.sizes:
                # If the key already exists, adjust the total size
                old_size = self.sizes[key]
                self.total_size -= old_size
            else:
                # New key: add to FIFO queue
                self.order.append(key)
                # Compute prefix once and store it in key_prefix
                if "_" in key:
                    prefix = key.split('_', 1)[0] + "_"
                else:
                    prefix = key
                self.key_prefix[key] = prefix
                self.prefix_index[prefix].add(key)
            # Save the size for this key and update total_size
            self.sizes[key] = size
            self.total_size += size

            # Increment the set counter for periodic eviction
            self._set_counter += 1

        # Idea 3: If using external backend, evict cache every _evict_interval
        # sets. Otherwise, always evict immediately.
        if self._set_counter >= self._evict_interval:
            with self.lock:
                self._set_counter = 0
            self._evict_cache()

    def get(self, key):
        """
        Get a value from the cache by key.

        Quickly retrieves a value from the cache by key.
        Here we simply request a value from the backend (either a dictionary or
        Django cache-backend) and return it without any additional operations.
        """
        if isinstance(self.cache, dict):
            return self.cache.get(key)
        else:
            packed_value = self.cache.get(key)
            if packed_value is None:
                return None
            try:
                return msgpack.unpackb(packed_value, raw=False)
            except Exception:
                # If unpacking fails, return what we got
                return packed_value

    def invalidate(self, prefix):
        """
        Invalidate model cache.

        Quickly removes all items from the cache whose keys start with prefix.
        Uses prefix_index for instant access to keys.
        When removing, each key's size is retrieved from self.sizes,
        and total_size is reduced by the corresponding amount.
        """
        prefix += '_'
        with self.lock:
            keys_to_remove = self.prefix_index.get(prefix, set())
            if not keys_to_remove:
                return

            # Remove keys from main cache and update total_size via sizes
            # dictionary
            if isinstance(self.cache, dict):
                for key in keys_to_remove:
                    self.cache.pop(key, None)
                    size = self.sizes.pop(key, 0)
                    self.total_size -= size
                    # Remove key from key_prefix as well
                    self.key_prefix.pop(key, None)
            else:
                # If using Django backend
                self.cache.delete_many(list(keys_to_remove))
                for key in keys_to_remove:
                    size = self.sizes.pop(key, 0)
                    self.total_size -= size
                    self.key_prefix.pop(key, None)

            # Remove prefix from index and update FIFO queue
            del self.prefix_index[prefix]
            self.order = deque(k for k in self.order if k not in keys_to_remove)

    def clear(self):
        """Clear cache completely."""
        with self.lock:
            if isinstance(self.cache, dict):
                self.cache.clear()
            else:
                self.cache.clear()
            self.order.clear()
            self.prefix_index.clear()
            self.sizes.clear()
            self.key_prefix.clear()
            self.total_size = 0

    def _evict_cache(self):
        """
        Perform FIFO cache evacuation.

        Removes old items until the total cache size is less than
        _CLEARINT_THESHOLD of the limit.
        """
        with self.lock:
            # Evict until total_size is below 80% of cache_limit
            target_size = _CLEARINT_THESHOLD * self.cache_limit
            while self.total_size > target_size and self.order:
                # Extract the oldest key from the queue (FIFO)
                key = self.order.popleft()

                # Delete entry from backend cache
                if isinstance(self.cache, dict):
                    self.cache.pop(key, None)
                else:
                    self.cache.delete(key)

                # Extract the size of the entry to be deleted and reduce
                # the overall cache size
                size = self.sizes.pop(key, 0)
                self.total_size -= size

                # Retrieve prefix from key_prefix without splitting
                prefix = self.key_prefix.pop(key, None)
                if prefix is not None:
                    self.prefix_index[prefix].discard(key)
                    if not self.prefix_index[prefix]:
                        del self.prefix_index[prefix]


# Global cache object (unique for the system)
treenode_cache = TreeCache()


# ---------------------------------------------------
# Decorator
# ---------------------------------------------------

def cached_method(func):
    """Decorate instance or class methods."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache = treenode_cache

        if isinstance(self, type):
            unique_id = to_base36(id(self))
            label = getattr(self._meta, 'label', self.__name__)
        else:
            unique_id = getattr(self, "pk", None) or to_base36(id(self))
            label = self._meta.label

        cache_key = cache.generate_cache_key(
            label,
            func.__name__,
            unique_id,
            *args,
            **kwargs
        )
        value = cache.get(cache_key)
        if value is None:
            value = func(self, *args, **kwargs)
            cache.set(cache_key, value)
        return value
    return wrapper


# The End
