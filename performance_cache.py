"""
Performance Caching System
Implements caching for expensive operations in sprite viewer.
Part of Phase 4 refactoring: Design Pattern Implementation.
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from collections import OrderedDict
import time
import weakref
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QObject, Signal


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def reset(self):
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size_bytes = 0


class CacheEntry:
    """Individual cache entry with metadata."""
    
    def __init__(self, key: str, value: Any, size_bytes: int):
        self.key = key
        self.value = value
        self.size_bytes = size_bytes
        self.created_time = time.time()
        self.last_access_time = self.created_time
        self.access_count = 0
    
    def access(self):
        """Update access metadata."""
        self.last_access_time = time.time()
        self.access_count += 1
    
    @property
    def age(self) -> float:
        """Age in seconds since creation."""
        return time.time() - self.created_time
    
    @property
    def time_since_access(self) -> float:
        """Time in seconds since last access."""
        return time.time() - self.last_access_time


class LRUCache:
    """Least Recently Used cache with size limit."""
    
    def __init__(self, max_size_mb: int = 100):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size_bytes = 0
        self._stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            # Move to end (most recently used)
            entry = self._cache.pop(key)
            entry.access()
            self._cache[key] = entry
            self._stats.hits += 1
            return entry.value
        
        self._stats.misses += 1
        return None
    
    def put(self, key: str, value: Any, size_bytes: int):
        """Add value to cache."""
        # Remove if already exists
        if key in self._cache:
            self._remove(key)
        
        # Evict entries if needed
        while self._current_size_bytes + size_bytes > self._max_size_bytes and self._cache:
            self._evict_lru()
        
        # Add new entry
        entry = CacheEntry(key, value, size_bytes)
        self._cache[key] = entry
        self._current_size_bytes += size_bytes
        self._stats.total_size_bytes = self._current_size_bytes
    
    def _remove(self, key: str):
        """Remove entry from cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size_bytes -= entry.size_bytes
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._current_size_bytes -= entry.size_bytes
            self._stats.evictions += 1
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._current_size_bytes = 0
        self._stats.total_size_bytes = 0
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats


class PixmapCache(QObject):
    """Specialized cache for QPixmap objects."""
    
    # Signals
    cacheHit = Signal(str)
    cacheMiss = Signal(str)
    cacheEviction = Signal(str)
    
    def __init__(self, max_size_mb: int = 200):
        super().__init__()
        self._cache = LRUCache(max_size_mb)
        self._weak_refs: Dict[str, weakref.ref] = {}
    
    def get_scaled_pixmap(self, original: QPixmap, scale: float, 
                         key_prefix: str = "") -> QPixmap:
        """Get scaled pixmap from cache or create new one."""
        # Create unique key
        key = f"{key_prefix}_{id(original)}_{scale:.3f}_{original.width()}x{original.height()}"
        
        # Check cache
        cached = self._cache.get(key)
        if cached is not None:
            self.cacheHit.emit(key)
            return cached
        
        # Check weak references (pixmap might still be in memory)
        weak_ref = self._weak_refs.get(key)
        if weak_ref is not None:
            pixmap = weak_ref()
            if pixmap is not None:
                # Re-add to cache
                self._cache.put(key, pixmap, self._estimate_pixmap_size(pixmap))
                self.cacheHit.emit(key)
                return pixmap
        
        # Create new scaled pixmap
        self.cacheMiss.emit(key)
        
        target_width = int(original.width() * scale)
        target_height = int(original.height() * scale)
        
        scaled = original.scaled(
            target_width, target_height,
            aspectMode=1,  # KeepAspectRatio
            transformMode=1  # SmoothTransformation
        )
        
        # Add to cache
        size_bytes = self._estimate_pixmap_size(scaled)
        self._cache.put(key, scaled, size_bytes)
        
        # Keep weak reference
        self._weak_refs[key] = weakref.ref(scaled)
        
        return scaled
    
    def get_frame_pixmap(self, sprite_sheet: QPixmap, frame_rect: Tuple[int, int, int, int],
                        key_prefix: str = "") -> QPixmap:
        """Get frame pixmap from cache or extract from sheet."""
        x, y, width, height = frame_rect
        key = f"{key_prefix}_frame_{x}_{y}_{width}x{height}"
        
        # Check cache
        cached = self._cache.get(key)
        if cached is not None:
            self.cacheHit.emit(key)
            return cached
        
        # Extract frame
        self.cacheMiss.emit(key)
        frame = sprite_sheet.copy(x, y, width, height)
        
        # Add to cache
        size_bytes = self._estimate_pixmap_size(frame)
        self._cache.put(key, frame, size_bytes)
        
        return frame
    
    def _estimate_pixmap_size(self, pixmap: QPixmap) -> int:
        """Estimate memory size of pixmap in bytes."""
        # Assume 4 bytes per pixel (RGBA)
        return pixmap.width() * pixmap.height() * 4
    
    def clear(self):
        """Clear all cached pixmaps."""
        self._cache.clear()
        self._weak_refs.clear()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._cache.get_stats()


class ComputationCache:
    """Generic cache for expensive computations."""
    
    def __init__(self, max_entries: int = 1000):
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._max_entries = max_entries
        self._stats = CacheStats()
    
    def get_or_compute(self, key: str, compute_func, *args, **kwargs) -> Any:
        """Get cached result or compute and cache."""
        if key in self._cache:
            # Move to end (most recently used)
            value, timestamp = self._cache.pop(key)
            self._cache[key] = (value, time.time())
            self._stats.hits += 1
            return value
        
        # Compute value
        self._stats.misses += 1
        value = compute_func(*args, **kwargs)
        
        # Add to cache
        self._add(key, value)
        
        return value
    
    def _add(self, key: str, value: Any):
        """Add value to cache with LRU eviction."""
        # Remove if already exists
        if key in self._cache:
            del self._cache[key]
        
        # Evict if at capacity
        if len(self._cache) >= self._max_entries:
            # Remove oldest
            self._cache.popitem(last=False)
            self._stats.evictions += 1
        
        # Add new entry
        self._cache[key] = (value, time.time())
    
    def invalidate(self, key: str):
        """Invalidate specific cache entry."""
        if key in self._cache:
            del self._cache[key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        import re
        regex = re.compile(pattern)
        keys_to_remove = [k for k in self._cache.keys() if regex.match(k)]
        for key in keys_to_remove:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats


class CacheManager(QObject):
    """Central manager for all application caches."""
    
    # Signals
    cacheCleared = Signal(str)  # cache_name
    statsUpdated = Signal(dict)  # stats by cache name
    
    def __init__(self):
        super().__init__()
        self._caches: Dict[str, Any] = {}
        self._pixmap_cache = PixmapCache()
        self._computation_cache = ComputationCache()
        
        # Register default caches
        self.register_cache('pixmap', self._pixmap_cache)
        self.register_cache('computation', self._computation_cache)
    
    def register_cache(self, name: str, cache: Any):
        """Register a cache instance."""
        self._caches[name] = cache
    
    def get_cache(self, name: str) -> Optional[Any]:
        """Get cache by name."""
        return self._caches.get(name)
    
    @property
    def pixmap_cache(self) -> PixmapCache:
        """Get pixmap cache instance."""
        return self._pixmap_cache
    
    @property
    def computation_cache(self) -> ComputationCache:
        """Get computation cache instance."""
        return self._computation_cache
    
    def clear_cache(self, name: str):
        """Clear specific cache."""
        cache = self._caches.get(name)
        if cache and hasattr(cache, 'clear'):
            cache.clear()
            self.cacheCleared.emit(name)
    
    def clear_all_caches(self):
        """Clear all registered caches."""
        for name, cache in self._caches.items():
            if hasattr(cache, 'clear'):
                cache.clear()
                self.cacheCleared.emit(name)
    
    def get_all_stats(self) -> Dict[str, CacheStats]:
        """Get statistics from all caches."""
        stats = {}
        
        for name, cache in self._caches.items():
            if hasattr(cache, 'get_stats'):
                stats[name] = cache.get_stats()
        
        self.statsUpdated.emit(stats)
        return stats
    
    def get_memory_usage_mb(self) -> float:
        """Get total memory usage of all caches in MB."""
        total_bytes = 0
        
        for cache in self._caches.values():
            if hasattr(cache, 'get_stats'):
                stats = cache.get_stats()
                if hasattr(stats, 'total_size_bytes'):
                    total_bytes += stats.total_size_bytes
        
        return total_bytes / (1024 * 1024)