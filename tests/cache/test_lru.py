import pytest
import time
from threading import Event

from pdfreader_reborn.cache import PageAdapter, PageCacheLRU


class ListAdapter:
    """Simple adapter backed by a list, for unit testing."""

    def __init__(self, pages: list[int]) -> None:
        self._pages = pages
        self.load_calls: list[int] = []

    @property
    def page_count(self) -> int:
        return len(self._pages)

    def load_page(self, index: int) -> int:
        self.load_calls.append(index)
        if index < 0 or index >= len(self._pages):
            raise IndexError(index)
        return self._pages[index]


class SlowAdapter:
    """Adapter with artificial delay for async testing."""

    def __init__(self, pages: list[int], delay: float = 0.05) -> None:
        self._pages = pages
        self._delay = delay
        self.load_calls: list[int] = []

    @property
    def page_count(self) -> int:
        return len(self._pages)

    def load_page(self, index: int) -> int:
        self.load_calls.append(index)
        time.sleep(self._delay)
        return self._pages[index]


# ── Basic operations ──────────────────────────────────────────


class TestPageCacheLRU:
    """Tests for basic LRU cache operations."""

    def test_empty_cache(self) -> None:
        """New cache should be empty."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        assert len(cache) == 0
        assert cache.size == 0

    def test_get_missing_returns_none(self) -> None:
        """get() on a missing key should return None."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        assert cache.get(0) is None

    def test_put_and_get(self) -> None:
        """put() then get() should return the value."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        cache.put(0, 10)
        assert cache.get(0) == 10
        assert len(cache) == 1

    def test_put_updates_existing(self) -> None:
        """put() with existing key should update the value."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        cache.put(0, 10)
        cache.put(0, 99)
        assert cache.get(0) == 99
        assert len(cache) == 1

    def test_contains(self) -> None:
        """in operator should work."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        cache.put(0, 10)
        assert 0 in cache
        assert 1 not in cache

    def test_remove(self) -> None:
        """remove() should delete the entry."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        cache.put(0, 10)
        assert cache.remove(0) is True
        assert cache.get(0) is None
        assert len(cache) == 0

    def test_remove_missing_returns_false(self) -> None:
        """remove() on missing key should return False."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        assert cache.remove(99) is False

    def test_clear(self) -> None:
        """clear() should remove all entries."""
        cache = PageCacheLRU(adapter=ListAdapter([10, 20, 30]))
        cache.put(0, 10)
        cache.put(1, 20)
        cache.clear()
        assert len(cache) == 0


# ── Capacity / eviction ──────────────────────────────────────


class TestPageCacheLRUEviction:
    """Tests for LRU eviction behavior."""

    def test_evicts_lru_when_full(self) -> None:
        """Cache should evict the least recently used page at capacity."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=3)
        cache.put(0, 0)
        cache.put(1, 1)
        cache.put(2, 2)
        assert len(cache) == 3

        # Adding a 4th page should evict page 0 (LRU).
        cache.put(3, 3)
        assert len(cache) == 3
        assert cache.get(0) is None
        assert cache.get(3) == 3

    def test_access_promotes_to_mru(self) -> None:
        """Accessing a page should promote it to MRU."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=3)
        cache.put(0, 0)
        cache.put(1, 1)
        cache.put(2, 2)

        # Access page 0 to promote it.
        cache.get(0)

        # Now page 1 is LRU. Adding page 3 should evict page 1.
        cache.put(3, 3)
        assert cache.get(0) == 0
        assert cache.get(1) is None

    def test_capacity_change_evicts_excess(self) -> None:
        """Reducing capacity should evict excess LRU pages."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=5)
        for i in range(5):
            cache.put(i, i)
        assert len(cache) == 5

        cache.capacity = 2
        assert cache.size == 2

    def test_invalid_capacity_raises(self) -> None:
        """Capacity < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="capacity must be >= 1"):
            PageCacheLRU(adapter=ListAdapter([10]), capacity=0)

    def test_invalid_capacity_setter_raises(self) -> None:
        """Setting capacity < 1 should raise ValueError."""
        cache = PageCacheLRU(adapter=ListAdapter([10]), capacity=5)
        with pytest.raises(ValueError, match="capacity must be >= 1"):
            cache.capacity = -1


# ── get_or_load ──────────────────────────────────────────────


class TestPageCacheLRUGetOrLoad:
    """Tests for get_or_load synchronous loading."""

    def test_get_or_load_calls_adapter(self) -> None:
        """get_or_load should call adapter.load_page for cache miss."""
        adapter = ListAdapter([10, 20, 30])
        cache = PageCacheLRU(adapter=adapter)
        value = cache.get_or_load(0)
        assert value == 10
        assert 0 in cache
        assert 0 in adapter.load_calls

    def test_get_or_load_returns_cached(self) -> None:
        """get_or_load should return cached value without calling adapter."""
        adapter = ListAdapter([10, 20, 30])
        cache = PageCacheLRU(adapter=adapter)
        cache.put(0, 99)
        adapter.load_calls.clear()
        value = cache.get_or_load(0)
        assert value == 99
        assert len(adapter.load_calls) == 0


# ── Distribution / compute_range ─────────────────────────────


class TestPageCacheLRUDistribution:
    """Tests for page distribution around focus."""

    def test_default_distribution_5(self) -> None:
        """With capacity=5, focus=10: start=8, end=13."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=5)
        start, end = cache.compute_range(10)
        assert start == 8
        assert end == 13  # 8,9,10,11,12

    def test_default_distribution_5_start(self) -> None:
        """Focus at 1 with capacity=5: start=0, end=4."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=5)
        start, end = cache.compute_range(1)
        assert start == 0
        assert end == 4

    def test_default_distribution_5_end(self) -> None:
        """Focus at last page with capacity=5: clamps to doc end."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=5)
        start, end = cache.compute_range(19)
        assert start == 17
        assert end == 20

    def test_asymmetric_split(self) -> None:
        """With capacity=4, before=1, after=2."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=4)
        start, end = cache.compute_range(10)
        assert start == 9  # 1 before
        assert end == 13  # 2 after + focus = 9,10,11,12

    def test_capacity_1(self) -> None:
        """With capacity=1, only the focus page is loaded."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=1)
        start, end = cache.compute_range(10)
        assert start == 10
        assert end == 11

    def test_focus_at_zero(self) -> None:
        """Focus at 0 should clamp start to 0."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=5)
        start, end = cache.compute_range(0)
        assert start == 0
        assert end == 3  # 0 + 2 (after) + 1

    def test_focus_uses_default(self) -> None:
        """compute_range() without args should use self.focus."""
        adapter = ListAdapter(list(range(20)))
        cache = PageCacheLRU(adapter=adapter, capacity=5)
        cache.focus = 10
        start, end = cache.compute_range()
        assert start == 8
        assert end == 13


# ── Linked list order ────────────────────────────────────────


class TestPageCacheLRULinkedOrder:
    """Tests that verify MRU→LRU ordering via keys property."""

    def test_keys_returns_mru_first(self) -> None:
        """keys should return pages in MRU → LRU order."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=3)
        cache.put(0, 0)
        cache.put(1, 1)
        cache.put(2, 2)
        # Most recent: 2, then 1, then 0
        assert cache.keys == [2, 1, 0]

    def test_get_promotes_key(self) -> None:
        """get() should move the key to the head (MRU)."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=3)
        cache.put(0, 0)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(0)  # promote 0
        assert cache.keys == [0, 2, 1]


# ── Callbacks ────────────────────────────────────────────────


class TestPageCacheLRUCallbacks:
    """Tests for eviction and load callbacks."""

    def test_evicted_callback(self) -> None:
        """on_evicted callback should fire when a page is evicted."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=2)
        evicted: list[int] = []
        cache.on_evicted(evicted.append)

        cache.put(0, 0)
        cache.put(1, 1)
        cache.put(2, 2)  # evicts 0
        assert evicted == [0]

    def test_loaded_callback(self) -> None:
        """on_loaded callback should fire when a page is put."""
        cache = PageCacheLRU(adapter=ListAdapter(list(range(10))), capacity=5)
        loaded: list[int] = []
        cache.on_loaded(loaded.append)

        cache.put(0, 0)
        cache.put(1, 1)
        assert loaded == [0, 1]


# ── Async preloading ─────────────────────────────────────────


class TestPageCacheLRUAsync:
    """Tests for async preloading via focus setter."""

    def test_focus_triggers_preload(self) -> None:
        """Setting focus should trigger async loading of neighbors."""
        adapter = SlowAdapter(list(range(20)), delay=0.02)
        cache = PageCacheLRU(adapter=adapter, capacity=5, max_workers=2)

        cache.focus = 10
        # Give threads time to complete.
        time.sleep(0.2)

        start, end = cache.compute_range(10)
        for i in range(start, end):
            assert i in cache, f"Page {i} should be cached"

        cache.shutdown()

    def test_async_pages_have_correct_values(self) -> None:
        """Async loaded pages should have the correct values."""
        adapter = SlowAdapter([i * 10 for i in range(20)], delay=0.02)
        cache = PageCacheLRU(adapter=adapter, capacity=5, max_workers=2)

        cache.focus = 5
        time.sleep(0.2)

        for i in range(3, 8):  # focus=5, capacity=5 → 3..7
            value = cache.get(i)
            assert value == i * 10, f"Page {i}: expected {i * 10}, got {value}"

        cache.shutdown()

    def test_shutdown_stops_threads(self) -> None:
        """shutdown() should stop the thread pool."""
        adapter = SlowAdapter(list(range(10)), delay=0.02)
        cache = PageCacheLRU(adapter=adapter, capacity=5)
        cache.shutdown()
        # Should not raise.
        cache.clear()


# ── Adapter protocol ─────────────────────────────────────────


class TestPageAdapter:
    """Tests for the PageAdapter protocol."""

    def test_list_adapter_satisfies_protocol(self) -> None:
        """ListAdapter should satisfy the PageAdapter protocol."""
        adapter = ListAdapter([10, 20, 30])
        assert isinstance(adapter, PageAdapter)

    def test_page_count_property(self) -> None:
        """Adapter should expose page_count."""
        adapter = ListAdapter([10, 20, 30])
        assert adapter.page_count == 3

    def test_load_page_returns_value(self) -> None:
        """load_page should return the page value."""
        adapter = ListAdapter([10, 20, 30])
        assert adapter.load_page(0) == 10
        assert adapter.load_page(2) == 30

    def test_load_page_out_of_range_raises(self) -> None:
        """load_page with out-of-range index should raise IndexError."""
        adapter = ListAdapter([10, 20, 30])
        with pytest.raises(IndexError):
            adapter.load_page(99)
