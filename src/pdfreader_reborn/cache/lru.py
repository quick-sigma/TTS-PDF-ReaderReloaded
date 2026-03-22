"""LRU page cache with doubly-linked list and async preloading.

The cache evicts the least-recently-used page when capacity is reached.
When the focus page changes, it preloads ``before`` pages behind and
``after`` pages ahead (where ``before = floor((max-1)/2)``).

Example::

    cache = PageCacheLRU(capacity=5, adapter=my_adapter)
    page = cache.get(10)          # loads synchronously if not cached
    cache.focus = 15              # triggers async preload of 13..17
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock
from typing import Generic, TypeVar

from pdfreader_reborn.cache.adapter import PageAdapter

K = int
V = TypeVar("V")

DEFAULT_CAPACITY = 5
DEFAULT_WORKERS = 2


class _Node(Generic[V]):
    """Doubly-linked list node.

    Attributes:
        key: Page index used as cache key.
        value: Cached page value.
        prev: Pointer to the previous (more-recently-used) node.
        next: Pointer to the next (less-recently-used) node.
    """

    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key: int, value: V) -> None:
        self.key = key
        self.value = value
        self.prev: _Node[V] | None = None
        self.next: _Node[V] | None = None


class PageCacheLRU(Generic[V]):
    """LRU cache for document pages with async preloading.

    Uses an O(1) doubly-linked list + hash map for eviction.  Page
    loads are delegated to a :class:`PageAdapter` running on a
    background ``ThreadPoolExecutor``.

    Args:
        capacity: Maximum pages in the cache.  Defaults to 5.
        adapter: A ``PageAdapter`` that loads pages by index.
        max_workers: Thread pool size for async preloading.
    """

    def __init__(
        self,
        adapter: PageAdapter[V],
        capacity: int = DEFAULT_CAPACITY,
        max_workers: int = DEFAULT_WORKERS,
    ) -> None:
        if capacity < 1:
            msg = f"capacity must be >= 1, got {capacity}"
            raise ValueError(msg)

        self._capacity = capacity
        self._adapter = adapter
        self._lock = Lock()

        # ── Doubly-linked list ───────────────────────────────
        self._head: _Node[V] | None = None  # MRU
        self._tail: _Node[V] | None = None  # LRU
        self._map: dict[K, _Node[V]] = {}

        # ── Async ────────────────────────────────────────────
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: dict[K, Future[V]] = {}
        self._generation: int = 0

        # ── Focus tracking ───────────────────────────────────
        self._focus: K = 0
        self._on_evicted: list = []
        self._on_loaded: list = []

    # ── Properties ───────────────────────────────────────────

    @property
    def capacity(self) -> int:
        """Return the maximum number of pages the cache can hold."""
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        """Update capacity and evict excess pages if shrinking."""
        if value < 1:
            msg = f"capacity must be >= 1, got {value}"
            raise ValueError(msg)
        evicted: list[K] = []
        with self._lock:
            self._capacity = value
            while len(self._map) > self._capacity:
                key = self._evict_lru()
                if key is not None:
                    evicted.append(key)
        for k in evicted:
            self._notify_evicted(k)

    @property
    def size(self) -> int:
        """Return the number of pages currently cached."""
        return len(self._map)

    @property
    def focus(self) -> K:
        """Return the current focus (center) page index."""
        return self._focus

    @focus.setter
    def focus(self, index: K) -> None:
        """Set the focus page and trigger async preload of neighbors."""
        self._focus = index
        self._preload_around(index)

    @property
    def keys(self) -> list[K]:
        """Return cached page indices in MRU → LRU order."""
        result: list[K] = []
        node = self._head
        while node is not None:
            result.append(node.key)
            node = node.next
        return result

    # ── Distribution ─────────────────────────────────────────

    def compute_range(self, focus: K | None = None) -> tuple[K, K]:
        """Return (start, end) for preloading around a focus page.

        With ``capacity=5`` and ``focus=10`` this returns ``(8, 13)``
        — loading pages 8, 9, 10, 11, 12.

        The distribution is asymmetric: ``before = floor((n-1)/2)``
        so with capacity 5 → before=2, after=2; with capacity 4 →
        before=1, after=2.

        Args:
            focus: Center page index.  Defaults to ``self.focus``.

        Returns:
            Tuple of (start_inclusive, end_exclusive).
        """
        if focus is None:
            focus = self._focus
        before = (self._capacity - 1) // 2
        after = self._capacity - 1 - before
        total = self._adapter.page_count
        start = max(0, focus - before)
        end = min(total, focus + after + 1)
        return (start, end)

    # ── Core operations ──────────────────────────────────────

    def get(self, key: K) -> V | None:
        """Retrieve a page by index.  Returns None if not cached."""
        with self._lock:
            node = self._map.get(key)
            if node is not None:
                self._move_to_head(node)
                return node.value
            return None

    def get_or_load(self, key: K) -> V:
        """Retrieve a page, loading it synchronously if needed."""
        with self._lock:
            node = self._map.get(key)
            if node is not None:
                self._move_to_head(node)
                return node.value

        value = self._adapter.load_page(key)
        self.put(key, value)
        return value

    def put(self, key: K, value: V) -> None:
        """Insert or update a page in the cache."""
        to_notify: list = []
        with self._lock:
            if key in self._map:
                node = self._map[key]
                node.value = value
                self._move_to_head(node)
            else:
                if len(self._map) >= self._capacity:
                    evicted_key = self._evict_lru()
                    if evicted_key is not None:
                        to_notify.append(("evicted", evicted_key))
                node = _Node(key, value)
                self._add_to_head(node)
                self._map[key] = node
                to_notify.append(("loaded", key))

        # Notify outside the lock to avoid deadlocks with callbacks.
        for kind, k in to_notify:
            if kind == "loaded":
                self._notify_loaded(k)
            else:
                self._notify_evicted(k)

    def remove(self, key: K) -> bool:
        """Remove a page from the cache.  Returns True if it was cached."""
        to_notify = False
        with self._lock:
            node = self._map.pop(key, None)
            if node is None:
                return False
            self._detach(node)
            to_notify = True
        if to_notify:
            self._notify_evicted(key)
        return True

    def clear(self) -> None:
        """Remove all pages from the cache and cancel pending futures."""
        with self._lock:
            self._generation += 1
            self._map.clear()
            self._head = None
            self._tail = None
            for f in self._futures.values():
                f.cancel()
            self._futures.clear()

    # ── Async preloading ─────────────────────────────────────

    def _preload_around(self, focus: K) -> None:
        """Asynchronously load pages around the focus index."""
        start, end = self.compute_range(focus)
        gen = self._generation

        # Cancel futures for pages outside the new range.
        for key in list(self._futures):
            if key < start or key >= end:
                self._futures.pop(key, None)

        for i in range(start, end):
            if i not in self._map and i not in self._futures:
                future = self._pool.submit(self._adapter.load_page, i)
                self._futures[i] = future
                future.add_done_callback(
                    lambda f, k=i, g=gen: self._on_page_loaded(k, f, g)
                )

    def _on_page_loaded(self, key: K, future: Future[V], gen: int) -> None:
        """Handle a page that finished loading.

        Discards results from a previous generation (i.e. submitted
        before the last ``clear()``).
        """
        if gen != self._generation:
            return
        self._futures.pop(key, None)
        if future.cancelled():
            return
        try:
            value = future.result()
            self.put(key, value)
        except Exception:
            pass

    # ── Eviction callbacks ───────────────────────────────────

    def on_evicted(self, fn) -> None:  # noqa: ANN001
        """Register a callback called when a page is evicted."""
        self._on_evicted.append(fn)

    def on_loaded(self, fn) -> None:  # noqa: ANN001
        """Register a callback called when a page is loaded."""
        self._on_loaded.append(fn)

    def _notify_evicted(self, key: K) -> None:
        for fn in self._on_evicted:
            fn(key)

    def _notify_loaded(self, key: K) -> None:
        for fn in self._on_loaded:
            fn(key)

    # ── Doubly-linked list helpers ───────────────────────────

    def _add_to_head(self, node: _Node[V]) -> None:
        node.prev = None
        node.next = self._head
        if self._head is not None:
            self._head.prev = node
        self._head = node
        if self._tail is None:
            self._tail = node

    def _detach(self, node: _Node[V]) -> None:
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self._head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self._tail = node.prev
        node.prev = None
        node.next = None

    def _move_to_head(self, node: _Node[V]) -> None:
        if node is self._head:
            return
        self._detach(node)
        self._add_to_head(node)

    def _evict_lru(self) -> K | None:
        if self._tail is None:
            return None
        node = self._tail
        self._detach(node)
        del self._map[node.key]
        return node.key

    # ── Context manager ──────────────────────────────────────

    def shutdown(self) -> None:
        """Shut down the thread pool and clear the cache."""
        self._pool.shutdown(wait=False)
        self.clear()

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key: K) -> bool:
        return key in self._map

    def __repr__(self) -> str:
        return (
            f"PageCacheLRU(capacity={self._capacity}, "
            f"size={self.size}, focus={self._focus})"
        )
