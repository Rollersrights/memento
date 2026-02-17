# TODO - Memento Development

*Last updated: 2026-02-17*
*Status: v0.2.0 released, working toward v0.3.0*

---

## 🔴 CRITICAL (Do First)

### Type Hints
- [ ] Add type hints to `scripts/store.py` - `MemoryStore` class methods
- [ ] Add type hints to `scripts/embed.py` - `embed()` function
- [ ] Add type hints to `scripts/cli.py` - all CLI functions
- [ ] Add type hints to `scripts/search.py` - search functions
- [ ] Create `scripts/types.py` for shared type definitions

**Example:**
```python
def recall(
    self,
    query: str,
    collection: Optional[str] = None,
    topk: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
```

### Test Coverage (Currently ~15%)
- [ ] Test `embed.py` - cache hit/miss, ONNX fallback
- [ ] Test `ingest.py` - document loading, chunking
- [ ] Test `search.py` - BM25 + vector hybrid
- [ ] Test `cli.py` - argument parsing, JSON output
- [ ] Test `compactor.py` - memory summarization
- [ ] Test edge cases: empty DB, malformed input, very long text
- [ ] Test concurrent access (threading)

### Error Handling
- [ ] Replace 8 bare `except:` clauses with specific exceptions
- [ ] Add try/except around SQLite operations with proper error messages
- [ ] Add input validation (sanitize user input)
- [ ] Wrap errors in custom `MementoError` class

---

## 🟡 IMPORTANT (Do Next)

### Logging Migration
- [ ] Replace `print()` with `logging` in `store.py`
- [ ] Replace `print()` with `logging` in `embed.py`
- [ ] Replace `print()` with `logging` in `dashboard.py`
- [ ] Add debug logging for cache hits/misses
- [ ] Add info logging for operations

**Pattern:**
```python
from scripts.logging_config import get_logger
logger = get_logger(__name__)
# Replace: print("Loading...")
# With:    logger.info("Loading...")
```

### Configuration System
- [ ] Create `~/.memento/config.yaml` support
- [ ] Add config validation with pydantic
- [ ] Support environment variable overrides
- [ ] Add config command to CLI (`memento config`)

### Documentation
- [ ] Add docstrings to all public methods
- [ ] Create API documentation (sphinx)
- [ ] Add architecture diagrams
- [ ] Write migration guide for schema changes

---

## 🟢 NICE TO HAVE (Later)

### Features
- [ ] REST API (FastAPI) for remote access
- [ ] Web UI (browser-based dashboard)
- [ ] Memory sync between nodes (federation)
- [ ] Import/export (JSON, CSV, Markdown)
- [ ] Full-text search improvements
- [ ] Query history / suggestions

### Performance
- [ ] Add query timeout option
- [ ] Add memory limits for vector cache
- [ ] Add pagination for results
- [ ] Async/await support for batch operations

### Packaging
- [ ] Docker image
- [ ] PyPI release (`pip install memento-memory`)
- [ ] Homebrew formula
- [ ] Debian/Ubuntu package

### DevEx
- [ ] Pre-commit hooks (black, flake8)
- [ ] Code coverage reporting (codecov)
- [ ] Performance benchmarks CI
- [ ] Integration tests

---

## 🐛 KNOWN ISSUES

1. **Model loading is slow** - 10s cold start (expected, ~22MB download)
2. **ONNX conversion not implemented** - stub exists but doesn't work yet
3. **No pagination** - `recall()` returns all results (fine for now, scale later)
4. **No query timeout** - could hang on very large databases

---

## 📋 COMPLETED ✅

- [x] Core memory storage (SQLite + NumPy)
- [x] Semantic search with MiniLM
- [x] LRU caching (500,000x speedup)
- [x] Persistent disk cache (Bob)
- [x] Hardware auto-detection (AVX2/ONNX)
- [x] Vector search backends (hnswlib/FAISS/NumPy)
- [x] Batch query optimization
- [x] CLI with rich output (Bob)
- [x] Test suite foundation (Bob)
- [x] CI/CD with GitHub Actions
- [x] Linting configuration (flake8)
- [x] Logging infrastructure
- [x] Packaging (pyproject.toml)
- [x] Documentation (README, INSTALL, CONTRIBUTING)

---

## 🎯 NEXT RELEASE (v0.3.0)

**Focus:** Foundation Hardening

**Must have:**
- Type hints on all public APIs
- Test coverage > 50%
- Error handling overhaul
- Logging migration complete

**Nice to have:**
- Config file support
- API documentation
- First PyPI release candidate

---

## 📝 NOTES

**Rita's focus areas:**
- Performance optimizations
- Cross-platform compatibility
- Infrastructure (CI/CD, packaging)

**Bob's focus areas:**
- Code quality (types, tests)
- CLI/UX improvements
- Documentation

**Both:**
- Security review
- Error handling
- Test coverage

---

*Pick an item, work on it, push to GitHub. Let's evolve Memento together!*
