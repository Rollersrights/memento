# Issue #20: Cache Warming Strategy

**Priority:** MEDIUM  
**Labels:** performance, enhancement, caching  
**Status:** Ready for Development

## Problem

Currently, the embedding cache only populates when queries are made. This means:
1. First-time queries suffer from cold cache latency (~10-50ms even with warm model)
2. Common queries (e.g., "what was I working on?", "what did Bob say?") get computed every session
3. No proactive strategy for keeping frequently-used embeddings warm

## Proposed Solution

Implement cache warming that:
1. **Pre-computes common query patterns** at startup
2. **Cron-friendly warmup script** for scheduled pre-loading
3. **Warmup API** for explicit cache warming via code
4. **Configurable query sets** for different use cases

## Implementation Details

### Phase 1: Warmup Function
```python
def warmup_cache(queries: List[str] = None, common_patterns: bool = True):
    """
    Pre-compute embeddings for common queries.
    
    Args:
        queries: Custom list of queries to warm
        common_patterns: Include common memory queries (default True)
    
    Common patterns to warm:
    - "What was I working on?"
    - "What did we discuss yesterday?"
    - "What are my tasks?"
    - "Summarize recent work"
    - "What did Bob say about X?"
    """
```

### Phase 2: Warmup Script
- `scripts/warmup.py` - CLI tool for cron jobs
- Returns exit code 0 on success
- JSON output for monitoring

### Phase 3: Auto-warmup Option
- `set_auto_warmup(minutes)` - Re-warm cache periodically
- Hook into model load to auto-warm common queries

## Acceptance Criteria

- [ ] `warmup_cache()` function implemented in `embed.py`
- [ ] CLI warmup script `warmup.py` created
- [ ] Common query patterns pre-loaded
- [ ] Warmup stats reported (queries warmed, time taken)
- [ ] Tests passing
- [ ] CHANGELOG.md updated

## Related Issues

- Issue #13 - Cold start latency (background model loading)
- Issue #19 - Model RAM management (unload after warmup?)

## Estimated Effort

~2 hours
