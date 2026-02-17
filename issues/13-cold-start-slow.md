# Performance Bottleneck #13: Cold Start Too Slow

**Priority:** 🔴 CRITICAL  
**Component:** Embedding / Model Loading  
**Labels:** `performance`, `bug`, `phase-1`

---

## Problem

First embedding query takes **10+ seconds** due to model loading:
- MiniLM model (22MB) loads from disk every cold start
- No pre-loading or background initialization
- User experience is terrible for first query

### Benchmark Data
```
Cold embed:  10,513ms (model loading + compute)
Warm embed:  0.04ms   (cache hit)
Speedup:     274,235x ⚡
```

The 274,000x speedup shows the problem - we're 10 seconds slow on cold start.

---

## Impact

- ❌ First query feels broken
- ❌ CLI feels unresponsive
- ❌ Cron jobs timeout
- ❌ User thinks system is broken

---

## Root Causes

1. **Lazy loading**: Model only loads on first `embed()` call
2. **No background thread**: Could load while system initializes
3. **No warm-up**: Could pre-compute common embeddings
4. **Model too big**: 22MB is heavy for embedded systems

---

## Solutions (in order of preference)

### Option 1: Background Pre-loader (RECOMMENDED)

Spawn thread on import to load model in background:
```python
# embed.py
_model_loading_thread = None
_model_ready = threading.Event()

def _load_model_async():
    global _embedder
    _embedder = AutoModel.from_pretrained(...)
    _model_ready.set()

# Start on module import
_model_loading_thread = threading.Thread(target=_load_model_async)
_model_loading_thread.daemon = True
_model_loading_thread.start()

def embed(text):
    _model_ready.wait(timeout=30)  # Wait for background load
    return _embedder(text)
```

**Pros:** 
- Non-blocking
- First query is instant if background finished
- Backward compatible

**Cons:**
- Uses RAM even before first query
- Slightly complex

### Option 2: Smaller Model

Switch to `paraphrase-MiniLM-L3-v2` (9MB vs 22MB):
- 2.4x smaller
- Similar quality for most tasks
- Faster loading

**Pros:**
- Simple change
- Less RAM

**Cons:**
- Quality trade-off
- Not always available

### Option 3: Lazy + Progress Indicator

Keep lazy loading but show progress:
```python
def embed(text):
    if _embedder is None:
        print("Loading model (one-time)...", file=sys.stderr)
        _load_model()
    return _embedder(text)
```

**Pros:**
- User knows what's happening
- Simple

**Cons:**
- Still slow first query

---

## Acceptance Criteria

- [ ] Cold start < 1000ms OR background loading hides latency
- [ ] Warm start still < 10ms
- [ ] No breaking API changes
- [ ] Works on older hardware (no AVX2 required)
- [ ] Tests pass

---

## Testing

```bash
# Test cold start
time python3 -c "from scripts.embed import embed; embed('test')"

# Should be < 1s or show progress immediately
```

---

## Related

- #12 - CLI visibility (we now show 💾 notifications)
- RFC-001 - Rust architecture (Phase 2a)

---

**Assigned to:** Autonomous worker  
**Target:** v0.2.2
