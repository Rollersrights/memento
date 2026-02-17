# Memento Development Discussion

> **Purpose:** Collaborative space for humans and agents to propose, discuss, and refine improvements to Memento.

## How to Use This File

1. **Add Ideas:** Create a new section with your proposal
2. **Tag Appropriately:** Use tags like `[IDEA]`, `[RESEARCH]`, `[QUESTION]`, `[DECISION_NEEDED]`
3. **Reference Issues:** Link to GitHub issues when relevant (#21, #22, etc.)
4. **Sign Your Entry:** Add your name/agent ID and date
5. **Update Status:** Mark items as [PENDING], [IN_PROGRESS], [COMPLETED], or [REJECTED]

---

## Active Discussions

### [2026-02-17] [DECISION_NEEDED] Cold Start Strategy - Bob

**Context:** Current cold start is 5-10s. Rust agent working on embedding engine for <2s target.

**Options:**
1. **Pure Rust** (current approach) - Best performance, most work
2. **Python + Pre-loaded ONNX** - Simpler, 2-3s achievable
3. **Hybrid** - Rust for critical path, Python fallback

**Decision needed:** Do we commit to full Rust or accept hybrid for faster delivery?

**Related:** #22 (Rust engine), #27 (cleanup)

**Status:** [IN_PROGRESS] - Rust agent working on it

---

### [2026-02-17] [IDEA] Simplified Auto-Store for OpenClaw - Brett

**Proposal:** Instead of complex significance detection, just store every conversation with:
- Raw text (user + agent)
- Timestamp
- Session ID
- Auto-calculated importance (length-based heuristic)

**Rationale:** Storage is cheap, search is fast. Better to capture everything than miss important context.

**Implementation:** Simple hook in OpenClaw that calls `memento remember` after each turn.

**Related:** #24 (OpenClaw hook)

**Status:** [PENDING] - Needs discussion on significance vs volume

---

### [2026-02-17] [RESEARCH] Embedding Model Upgrade Path - Research Agent

**Findings:**
- Current: all-MiniLM-L6-v2 (22M params, 384-dim)
- Option A: EmbeddingGemma-300M (300M params, 100+ langs)
- Option B: BGE-M3 (multilingual, late interaction)
- Option C: Jina-v2 (MRL support, 8K context)

**Recommendation:** Stay with MiniLM for now (fastest), add MRL support (#30) for flexibility, then evaluate upgrade.

**Related:** #30 (MRL), RESEARCH/papers/AI_MEMORY_TECH_2026.md

**Status:** [COMPLETED] - Decision documented

---

## Completed Discussions

### [2026-02-17] [DECISION] Database Location - Bob

**Decision:** Unified to `~/.openclaw/memento/`

**Rationale:**
- Single source of truth
- Follows XDG conventions
- Easy to backup
- Clear separation from other tools

**Implementation:** Done in commit e921817

**Related:** #29

---

## Research Backlog

### [PENDING] Quantization Impact Study

**Question:** What's the real accuracy impact of INT8 quantization on our specific use case?

**Experiment Needed:**
1. Embed 1000 test queries with FP32
2. Embed same with INT8
3. Compare recall@10 scores
4. Measure speed improvement

**Owner:** TBD
**Related:** #31

---

### [PENDING] Temporal Decay Function

**Question:** What decay function best matches human forgetting?

**Options:**
- Exponential: `e^(-λt)`
- Power law: `t^(-β)`
- Ebbinghaus: Custom curve

**Needs:** Literature review + user study

**Related:** #33

---

## Quick Reference

### Priority Labels
- **P0:** Critical - blocks release
- **P1:** Important - should have
- **P2:** Nice to have - future work

### Status Labels
- **[PENDING]:** Awaiting decision/resources
- **[IN_PROGRESS]:** Being worked on
- **[COMPLETED]:** Done and verified
- **[REJECTED]:** Decided against

### How to Add an Entry

```markdown
### [YYYY-MM-DD] [TAG] Title - Name

**Context:** Brief background

**Proposal/Idea/Question:** Detailed description

**Related:** #issue-numbers

**Status:** [STATUS]
```

---

*Last updated: 2026-02-17 by Bob*
*Next review: 2026-02-24*
