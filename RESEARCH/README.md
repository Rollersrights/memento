# Memento Research Index

## Research Papers

| Date | Title | File | Status |
|------|-------|------|--------|
| 2026-02-17 | AI Memory Technologies Research Report 2026 | [papers/AI_MEMORY_TECH_2026.md](papers/AI_MEMORY_TECH_2026.md) | Complete |

### Key Findings Summary

**Vector Databases:**
- ✅ sqlite-vec selected for local-first (zero dependencies, SQLite-native)
- Alternative: pgvector for PostgreSQL integration

**Embedding Models:**
- Current: all-MiniLM-L6-v2 (22M params, 384-dim)
- Future options: EmbeddingGemma-300M, BGE-M3, Jina-v2
- MRL (Matryoshka) enables flexible dimension truncation

**Memory Architectures:**
- MemGPT-style 3-tier hierarchy: Working → Episodic → Semantic
- Temporal decay mimics human forgetting
- Hybrid search: Vector + BM25 + Metadata

**Quantization:**
- INT8: 75% memory reduction, minimal accuracy loss
- FP8/NVFP4: Emerging standards for 2026

---

## Experiments

| Date | Experiment | File | Result |
|------|------------|------|--------|
| 2026-02-17 | ONNX Export | See memento/scripts/export_onnx.py | Success - 88MB model |
| 2026-02-17 | sqlite-vec Integration | memento/store.py | Success - 10-100x speedup |

### Pending Experiments

- [ ] INT8 quantization accuracy test (#31)
- [ ] Temporal decay function comparison (#33)
- [ ] Rust vs Python embedding speed (#22)
- [ ] WASM compilation test (#35)

---

## Architecture Decisions

| Date | Decision | File | Rationale |
|------|----------|------|-----------|
| 2026-02-17 | Database location | [decisions/001-database-location.md](decisions/001-database-location.md) | Single source of truth at ~/.openclaw/memento/ |
| 2026-02-17 | ONNX-only embedding | [decisions/002-onnx-only.md](decisions/002-onnx-only.md) | Remove PyTorch fallback for simplicity |
| 2026-02-17 | sqlite-vec backend | [decisions/003-sqlite-vec-only.md](decisions/003-sqlite-vec-only.md) | Remove numpy fallback |

### Decision Template

```markdown
# DECISION-XXX: Title

**Status:** [PROPOSED|ACCEPTED|REJECTED|DEPRECATED]
**Date:** YYYY-MM-DD
**Decision Maker:** Name

## Context
What is the issue we're deciding?

## Options Considered
1. Option A - Pros/Cons
2. Option B - Pros/Cons

## Decision
What we chose and why.

## Consequences
What becomes easier/harder.

## Related
- GitHub Issue: #XX
- Discussion: DISCUSSION.md section
```

---

## Adding Research

1. **Create file:** `RESEARCH/{papers,experiments,decisions}/YYYY-MM-DD-title.md`
2. **Update this index**
3. **Add to DISCUSSION.md** if actionable
4. **Create GitHub issue** for implementation tasks

---

*Research drives development. Document everything.*
