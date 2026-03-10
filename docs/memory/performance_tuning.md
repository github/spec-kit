# Performance Tuning Guide (T081)

## Scalability Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Memory entries per project | 1000+ | Count lines in memory files |
| Headers-first read time | <100ms | Time read_headers_first() call |
| Deep read time | <500ms | Time read_section() call |
| Search time (local) | <200ms | Time cross-project search |
| Vector search time | <1s | Time RAG query (with Ollama) |

## Optimization Strategies

### 1. Lazy Loading (Already Implemented)

```python
# GOOD: Only read headers
headers = reader.read_headers_first("lessons")

# BAD: Read entire file
content = Path("lessons.md").read_text()
```

### 2. Caching

#### Headers Cache (In-Memory)
```python
# Cache headers for 5 minutes
@lru_cache(maxsize=128, ttl=300)
def read_headers_first(file_type: str) -> List[Dict]:
    ...
```

#### Search Results Cache
```python
# Cache AI search results for 2 hours
def search_with_cache(query: str):
    cached = cache.get(f"search:{query}")
    if cached and cached['age'] < 7200:
        return cached['results']
    # Perform search...
```

### 3. Index-Based Search

#### Title Index (maintained incrementally)
```json
{
  "index_version": 1,
  "entries": [
    {"title": "JWT Fix", "file": "lessons", "offset": 1234},
    {"title": "Auth Pattern", "file": "patterns", "offset": 5678}
  ]
}
```

### 4. Parallel Reads

```python
# Read multiple file types in parallel
import concurrent.futures

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(read_headers, "lessons"): "lessons",
        executor.submit(read_headers, "patterns"): "patterns",
        executor.submit(read_headers, "architecture"): "architecture"
    }
    results = {futures[f]: f.result() for f in as_completed(futures)}
```

### 5. Compression

For large memory files (>100KB):
```bash
# Compress old entries
gzip -c lessons.md > lessons.md.gz

# Search compressed files
zgrep "pattern" lessons.md.gz
```

## Performance Monitoring

### Add Timing Decorator

```python
import time
from functools import wraps

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        if elapsed > 0.1:  # Log slow operations
            logger.warning(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper

@timed
def read_headers_first(file_type: str):
    ...
```

### Performance Metrics

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)

    def record(self, operation: str, duration: float):
        self.metrics[operation].append(duration)

    def summary(self) -> Dict:
        return {
            op: {
                "avg": sum(durs) / len(durs),
                "max": max(durs),
                "count": len(durs)
            }
            for op, durs in self.metrics.items()
        }
```

## Large-Scale Optimizations

### For 1000+ Entries

1. **Split by time**: lessons-2024.md, lessons-2023.md
2. **Split by category**: lessons-security.md, lessons-performance.md
3. **Database migration**: SQLite for 10K+ entries

### For Vector Search

1. **Batch embeddings**: Process 100 entries at once
2. **Background indexing**: Index new entries asynchronously
3. **Hierarchical search**: Search current project first, then global

## Benchmark Results

### Test Setup
- 500 memory entries
- 10 projects
- Local Ollama embedding (nomic-embed-text)

### Results (Target)

| Operation | Target | Notes |
|-----------|--------|-------|
| Read headers | <50ms | 3 files, 500 entries |
| Search local | <150ms | String matching |
| Search vector | <800ms | Ollama embedding + similarity |
| Cross-project | <300ms | 3 projects |
| Write entry | <100ms | Append to file |

## When to Optimize

### Don't Optimize Yet If
- <100 entries per project
- Search feels fast enough
- No user complaints

### Optimize When
- Headers read >200ms
- Search >1s
- Memory files >1MB
- User reports slowness

## Optimization Checklist

- [ ] Profile slow operations
- [ ] Add caching for hot paths
- [ ] Implement parallel I/O
- [ ] Compress old entries
- [ ] Add performance monitoring
- [ ] Set up benchmarks
- [ ] Document baseline metrics
