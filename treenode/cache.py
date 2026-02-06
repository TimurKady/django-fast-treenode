# -*- coding: utf-8 -*-
"""
TreeCache: High-performance asynchronous in-memory cache with memory size limits

Description:
- FIFO-based cache eviction controlled by total memory footprint (in bytes)
- Background thread performs serialization and memory tracking
- Supports prefix-based invalidation and full cache reset
- Fast and flexible, built for caching arbitrary Python objects

Usage:
- Call `set(key, value)` to queue data for caching
- Background worker will serialize and insert it
- Call `get(key)` to retrieve and deserialize cached values
- Use `invalidate(prefix)` to remove all keys with the given prefix
- Use `clear()` to fully reset the cache
- Don't forget to call `start_worker()` on initialization, and `stop_worker()`
  on shutdown

Dependencies:
- cloudpickle (faster and more flexible than standard pickle)

Version: 3.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""

import sys
import msgpack
import functools
import hashlib
import threading
import time
from collections import deque, defaultdict
from typing import Any, Callable

from .settings import CACHE_LIMIT


class TreeCache:
    """Tree Cache Class."""

    def __init__(self):
        """Initialize TreeCache with background worker and memory limit."""
        self.max_size = CACHE_LIMIT

        self.cache = {}                # key -> serialized value
        self.order = deque()           # FIFO order tracking
        self.queue_index = {}
        self.sizes = {}                # key -> size in bytes
        self.total_size = 0            # total size in bytes
        self.prefix_index = defaultdict(set)  # prefix -> keys
        self.key_prefix = {}           # key -> prefix

        self.queue = deque()           # write queue (key, value)
        self.queue_lock = threading.Lock()

        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.start_worker()

    def start_worker(self):
        """Start the background worker thread."""
        if not self.worker.is_alive():
            self.worker.start()

    def stop_worker(self):
        """Stop the background worker thread."""
        self.stop_event.set()
        self.worker.join()

    def _estimate_size(self, value):
        """
        Determine the size of the object in bytes.

        If the value is already in bytes or bytearray, simply returns its
        length. Otherwise, uses sys.getsizeof for an approximate estimate.
        """
        try:
            return int(len(msgpack.packb(value)) * 2.5)
        except Exception:
            return sys.getsizeof(value)

    def _worker_loop(self):
        """
        Loop Worker.

        Background worker that processes the cache queue,
        serializes values, and enforces memory constraints.
        """
        while not self.stop_event.is_set():
            with self.queue_lock:
                if self.queue:
                    key, value = self.queue.popleft()
                else:
                    key = value = None

            if key is not None:
                obj_size = self._estimate_size(value)
                self.cache[key] = value
                self.order.append(key)
                self.sizes[key] = obj_size
                self.total_size += obj_size

                prefix = key.split("|", 1)[0] + "|"
                self.key_prefix[key] = prefix
                self.prefix_index[prefix].add(key)

                # Clean queue_index after moving to cache
                self.queue_index.pop(key, None)

                if self.total_size > self.max_size:
                    self._evict_cache()
            else:
                time.sleep(0.0025)

    def set(self, key: str, value: Any):
        """Queue a key-value pair for caching. Actual insertion is async."""
        with self.queue_lock:
            self.queue.append((key, value))
            self.queue_index[key] = value

    def get(self, key: str) -> Any:
        """
        Get data from the cache.

        Retrieve a value from the cache and deserialize it.
        Returns None if key is not present or deserialization fails.
        """
        # Step 1. Try get value from the cache
        from_cache = self.cache.get(key)
        if from_cache is not None:
            return from_cache

        # Step 2. Search in pending queue
        return self.queue_index.get(key)

    def _evict_cache(self):
        """Remove oldest entries from the cache and auxiliary index."""
        while self.total_size > self.max_size and self.order:
            oldest = self.order.popleft()
            self.total_size -= self.sizes.pop(oldest, 0)
            self.cache.pop(oldest, None)
            prefix = self.key_prefix.pop(oldest, None)
            if prefix:
                self.prefix_index[prefix].discard(oldest)
            if hasattr(self, "queue_index"):
                self.queue_index.pop(oldest, None)

    def invalidate(self, prefix: str):
        """
        Invalidate all keys with the given prefix (e.g. "node_").

        Also purges pending items in the queue and queue_index with
        the same prefix.
        """
        prefix = f"{prefix}|"
        keys_to_remove = self.prefix_index.pop(prefix, set())
        for key in keys_to_remove:
            self.total_size -= self.sizes.pop(key, 0)
            self.cache.pop(key, None)
            self.key_prefix.pop(key, None)
            try:
                self.order.remove(key)
            except ValueError:
                pass
        with self.queue_lock:
            self.queue = deque(
                [(k, v) for k, v in self.queue if not k.startswith(prefix)])
            # Clean queue_index for all keys matching the prefix
            stale_keys = [k for k in self.queue_index if k.startswith(prefix)]
            for k in stale_keys:
                del self.queue_index[k]

    def clear(self):
        """Fully reset the cache, indexes, and the background queue."""
        self.cache.clear()
        self.order.clear()
        self.sizes.clear()
        self.total_size = 0
        self.prefix_index.clear()
        self.key_prefix.clear()
        with self.queue_lock:
            self.queue.clear()
            self.queue_index.clear()

    def info(self) -> dict:
        """Return runtime statistics for monitoring and diagnostics."""
        with self.queue_lock:
            queued = len(self.queue)

        return {
            "total_keys": len(self.cache),
            "queued_items": queued,
            "total_size": int(10*self.total_size/(1024*1024))/10,
            "max_size": int(10*self.max_size/(1024*1024))/10,
            "fill_percent": round(self.total_size / self.max_size * 100, 2) if self.max_size else 0.0,  # noqa: D501
            "prefixes": len(self.prefix_index),
            "running": not self.stop_event.is_set(),
            "thread_alive": self.worker.is_alive()
        }

    def generate_cache_key(self, label: str, func_name: str, unique_id: int,
                           args: tuple, kwargs: dict) -> str:
        """
        Generate a unique cache key for a function call.

        - Fast-path: for simple positional arguments, avoid serialization.
        - Full-path: use pickle+blake2b hash for complex inputs.
        """
        if not args and not kwargs:
            return f"{label}|{func_name}:{unique_id}:empty"

        try:
            key_data = (args, kwargs)
            packed = msgpack.packb(key_data)
            key = hashlib.blake2b(packed, digest_size=8).hexdigest()
            return f"{label}|{func_name}:{unique_id}:{key}"
        except Exception:
            fallback = repr((args, kwargs)).encode()
            key = hashlib.sha1(fallback).hexdigest()
            return f"{label}|{func_name}:{unique_id}:{key}"


# Global singleton cache instance
treenode_cache = TreeCache()


def cached_method(func: Callable) -> Callable:
    """
    Decorate method.

    Method decorator that caches results on a per-instance basis using
    TreeCache. The cache key includes the method, arguments, and instance ID.
    """
    cache = treenode_cache

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        label = self._meta.label
        unique_id = getattr(self, "pk", None) or id(self)
        func_name = func.__name__
        key = cache.generate_cache_key(
            label, func_name, unique_id, args, kwargs)
        result = cache.get(key)
        if result is None:
            result = func(self, *args, **kwargs)
            cache.set(key, result)
        return result
    return wrapper
