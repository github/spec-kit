"""
Performance optimization utilities for Bicep generator.

This module provides caching, async optimization, and performance monitoring
capabilities to improve the efficiency of template generation and validation.
"""

import asyncio
import functools
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from rich.console import Console
from rich.table import Table

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

console = Console()


@dataclass
class CacheEntry:
    """Represents a cached value with metadata."""
    
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl_seconds
    
    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": f"{self.hit_rate:.2f}%",
            "total_size_bytes": self.total_size_bytes,
            "entry_count": self.entry_count
        }


class LRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache with TTL support.
    
    Features:
    - Maximum size limit with automatic eviction
    - Time-to-live (TTL) expiration
    - Access statistics tracking
    - Memory usage monitoring
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
        max_memory_mb: int = 100
    ):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live for entries in seconds
            max_memory_mb: Maximum memory usage in megabytes
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired(self.ttl_seconds):
                # Remove expired entry
                self._remove_entry(key)
                self._stats.misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats.hits += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # Calculate size
            size_bytes = self._estimate_size(value)
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Evict entries if needed
            while (
                len(self._cache) >= self.max_size or
                self._stats.total_size_bytes + size_bytes > self.max_memory_bytes
            ):
                if not self._cache:
                    break
                self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                size_bytes=size_bytes
            )
            
            self._cache[key] = entry
            self._stats.entry_count = len(self._cache)
            self._stats.total_size_bytes += size_bytes
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._stats.entry_count = 0
            self._stats.total_size_bytes = 0
    
    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        async with self._lock:
            self._stats.entry_count = len(self._cache)
            return self._stats
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry and update stats."""
        entry = self._cache.pop(key, None)
        if entry:
            self._stats.total_size_bytes -= entry.size_bytes
            self._stats.entry_count = len(self._cache)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._cache:
            key, _ = self._cache.popitem(last=False)
            self._stats.evictions += 1
            self._stats.entry_count = len(self._cache)
    
    @staticmethod
    def _estimate_size(obj: Any) -> int:
        """Estimate object size in bytes."""
        try:
            # Simple size estimation
            if isinstance(obj, str):
                return len(obj.encode('utf-8'))
            elif isinstance(obj, (list, tuple)):
                return sum(LRUCache._estimate_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sum(
                    LRUCache._estimate_size(k) + LRUCache._estimate_size(v)
                    for k, v in obj.items()
                )
            else:
                # Fallback: use JSON serialization size
                return len(json.dumps(obj, default=str).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate


# Global cache instances
_schema_cache = LRUCache(max_size=500, ttl_seconds=3600, max_memory_mb=50)
_analysis_cache = LRUCache(max_size=100, ttl_seconds=1800, max_memory_mb=30)
_validation_cache = LRUCache(max_size=200, ttl_seconds=900, max_memory_mb=20)


def cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create deterministic key from args and kwargs
    key_data = {
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    key_json = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.sha256(key_json.encode()).hexdigest()[:16]
    
    return key_hash


def cached(
    cache: LRUCache,
    key_prefix: str = "",
    skip_cache: Optional[Callable[..., bool]] = None
) -> Callable[[F], F]:
    """
    Decorator for caching function results.
    
    Args:
        cache: LRU cache instance to use
        key_prefix: Prefix for cache keys
        skip_cache: Optional function to determine if caching should be skipped
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if we should skip cache
            if skip_cache and skip_cache(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, run async cache operations
            loop = asyncio.get_event_loop()
            
            # Check if we should skip cache
            if skip_cache and skip_cache(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Generate cache key
            key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = loop.run_until_complete(cache.get(key))
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            loop.run_until_complete(cache.set(key, result))
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
    
    return decorator


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    
    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    memory_delta_mb: float = 0.0
    items_processed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "operation": self.operation,
            "duration_ms": f"{self.duration_ms:.2f}",
            "timestamp": self.timestamp.isoformat(),
            "memory_delta_mb": f"{self.memory_delta_mb:.2f}",
            "items_processed": self.items_processed
        }


class PerformanceMonitor:
    """
    Monitor and track performance metrics.
    
    Features:
    - Operation timing
    - Memory usage tracking
    - Performance history
    - Statistical analysis
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: List[PerformanceMetrics] = []
        self._lock = asyncio.Lock()
    
    async def record(self, metrics: PerformanceMetrics) -> None:
        """
        Record performance metrics.
        
        Args:
            metrics: Performance metrics to record
        """
        async with self._lock:
            self.metrics.append(metrics)
            
            # Keep only recent metrics (last 1000)
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
    
    async def get_summary(
        self,
        operation: Optional[str] = None,
        recent_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Args:
            operation: Filter by operation name
            recent_minutes: Include only metrics from last N minutes
            
        Returns:
            Performance summary dictionary
        """
        async with self._lock:
            # Filter metrics
            cutoff = datetime.now() - timedelta(minutes=recent_minutes)
            filtered = [
                m for m in self.metrics
                if m.timestamp >= cutoff and (operation is None or m.operation == operation)
            ]
            
            if not filtered:
                return {
                    "count": 0,
                    "operation": operation,
                    "recent_minutes": recent_minutes
                }
            
            # Calculate statistics
            durations = [m.duration_ms for m in filtered]
            
            return {
                "count": len(filtered),
                "operation": operation,
                "recent_minutes": recent_minutes,
                "duration_ms": {
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "total": sum(durations)
                },
                "items_processed": sum(m.items_processed for m in filtered)
            }
    
    async def clear(self) -> None:
        """Clear all metrics."""
        async with self._lock:
            self.metrics.clear()


# Global performance monitor
_performance_monitor = PerformanceMonitor()


class PerformanceTimer:
    """
    Context manager for timing operations.
    
    Example:
        async with PerformanceTimer("schema_fetch") as timer:
            result = await fetch_schema()
        
        print(f"Operation took {timer.duration_ms}ms")
    """
    
    def __init__(
        self,
        operation: str,
        auto_record: bool = True,
        items_processed: int = 0
    ):
        """
        Initialize performance timer.
        
        Args:
            operation: Operation name
            auto_record: Automatically record metrics
            items_processed: Number of items processed
        """
        self.operation = operation
        self.auto_record = auto_record
        self.items_processed = items_processed
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
    
    async def __aenter__(self) -> 'PerformanceTimer':
        """Start timer."""
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timer and optionally record metrics."""
        self.end_time = time.perf_counter()
        
        if self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000
        
        if self.auto_record:
            metrics = PerformanceMetrics(
                operation=self.operation,
                duration_ms=self.duration_ms,
                items_processed=self.items_processed
            )
            await _performance_monitor.record(metrics)


async def batch_async(
    items: List[T],
    async_func: Callable[[T], Any],
    batch_size: int = 10,
    max_concurrent: int = 5
) -> List[Any]:
    """
    Process items in batches asynchronously with concurrency limit.
    
    Args:
        items: Items to process
        async_func: Async function to apply to each item
        batch_size: Number of items per batch
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of results
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(item: T) -> Any:
        async with semaphore:
            return await async_func(item)
    
    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_with_limit(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)
    
    return results


async def clear_all_caches() -> None:
    """Clear all performance caches."""
    await _schema_cache.clear()
    await _analysis_cache.clear()
    await _validation_cache.clear()
    
    console.print("[green]✓[/green] All caches cleared")


async def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics for all caches.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        "schema_cache": (await _schema_cache.get_stats()).to_dict(),
        "analysis_cache": (await _analysis_cache.get_stats()).to_dict(),
        "validation_cache": (await _validation_cache.get_stats()).to_dict()
    }


async def get_performance_summary(
    operation: Optional[str] = None,
    recent_minutes: int = 60
) -> Dict[str, Any]:
    """
    Get performance summary.
    
    Args:
        operation: Filter by operation name
        recent_minutes: Include only metrics from last N minutes
        
    Returns:
        Performance summary dictionary
    """
    return await _performance_monitor.get_summary(operation, recent_minutes)


def display_cache_stats(stats: Dict[str, Any]) -> None:
    """
    Display cache statistics in formatted table.
    
    Args:
        stats: Cache statistics dictionary
    """
    table = Table(title="Cache Statistics")
    
    table.add_column("Cache", style="cyan")
    table.add_column("Hit Rate", style="green")
    table.add_column("Entries", style="yellow")
    table.add_column("Size (bytes)", style="magenta")
    table.add_column("Hits", style="blue")
    table.add_column("Misses", style="red")
    
    for cache_name, cache_stats in stats.items():
        table.add_row(
            cache_name.replace('_', ' ').title(),
            cache_stats['hit_rate'],
            str(cache_stats['entry_count']),
            str(cache_stats['total_size_bytes']),
            str(cache_stats['hits']),
            str(cache_stats['misses'])
        )
    
    console.print(table)


def display_performance_summary(summary: Dict[str, Any]) -> None:
    """
    Display performance summary in formatted table.
    
    Args:
        summary: Performance summary dictionary
    """
    if summary['count'] == 0:
        console.print("[yellow]No performance metrics available[/yellow]")
        return
    
    table = Table(title=f"Performance Summary - {summary.get('operation', 'All Operations')}")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Operation Count", str(summary['count']))
    table.add_row("Time Period", f"Last {summary['recent_minutes']} minutes")
    table.add_row("Items Processed", str(summary['items_processed']))
    
    if 'duration_ms' in summary:
        duration = summary['duration_ms']
        table.add_row("Min Duration (ms)", f"{duration['min']:.2f}")
        table.add_row("Max Duration (ms)", f"{duration['max']:.2f}")
        table.add_row("Avg Duration (ms)", f"{duration['avg']:.2f}")
        table.add_row("Total Duration (ms)", f"{duration['total']:.2f}")
    
    console.print(table)


# Export cache instances for use in other modules
schema_cache = _schema_cache
analysis_cache = _analysis_cache
validation_cache = _validation_cache
performance_monitor = _performance_monitor
