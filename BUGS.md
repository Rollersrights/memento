# Memento Bug Tracker

Filed 2026-02-17 during comprehensive QA testing.

## P0 — Critical

| # | Title | Filed |
|---|-------|-------|
| #36 | `recall()` crashes in non-main threads — SIGALRM incompatible with threading | ✅ |
| #39 | All 5 existing test files broken — import from deleted `scripts/` path | ✅ |

## P1 — High

| # | Title | Filed |
|---|-------|-------|
| #37 | `unload_model()` crashes with UnboundLocalError for `_idle_timer` | ✅ |
| #38 | ONNX batch embedding fails with shape mismatch, loads PyTorch (~1.3GB RSS) | ✅ |

## P2 — Medium

| # | Title | Filed |
|---|-------|-------|
| #40 | Rate limiter uses global state — not test-isolated, shared across store instances | ✅ |
| #41 | `delete()` does not clean up FTS5 index entries | ✅ |
| #42 | FTS5 sync uses wrong `last_insert_rowid()` in `remember()` | ✅ |

## Summary

- **7 bugs found** during testing
- **2 P0** (block real-world usage)
- **2 P1** (significant impact)
- **3 P2** (correctness issues, non-blocking)
