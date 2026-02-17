# GitHub Issues to Create

*Use GitHub web interface or CLI to create these properly*

---

## P0 - Immediate

### Issue #1: [P0] Clean up legacy scripts/ folder
**Labels:** `cleanup`, `technical-debt`, `P0`  
**Assignee:** @Bob

**Body:**
```
## Problem
The codebase has 12,610 lines of Python but should be "small and beautiful". The `scripts/` folder contains legacy, duplicate, and outdated code that:
- Duplicates functionality in `memento/` package
- Causes import path confusion
- Breaks tests that reference wrong paths
- Increases maintenance burden

## Proposed Solution
1. Archive legacy code: `mkdir -p archive/legacy-scripts-$(date +%Y%m%d) && cp -r scripts/* archive/`
2. Remove legacy folders: `rm -rf scripts/ scripts.backup.*/`
3. Fix any remaining imports to use `memento.` package

## Acceptance Criteria
- [ ] `scripts/` folder removed from repo
- [ ] `scripts.backup.*/` folders removed
- [ ] All imports use `memento.` package only
- [ ] Tests still pass
- [ ] Archive folder created for reference
```

---

### Issue #2: [P0] Fix failing test suite - only 40% pass rate
**Labels:** `bug`, `testing`, `P0`  
**Assignee:** @Rita

**Body:**
```
## Problem
Test suite is failing with only 10/25 tests passing (40% pass rate). This blocks CI/CD.

## Current Failures
- test_cache.py: 2 failures (import path issues)
- test_embed_cache.py: 5 failures (missing sentence-transformers)
- test_store_edge_cases.py: 7 failures (various)

## Root Causes
1. Missing dependencies (sentence-transformers)
2. Import paths point to `scripts.embed` instead of `memento.embed`
3. Test environment not isolated

## Proposed Solution
1. Add `tests/conftest.py` with fixtures
2. Fix all imports to use `memento.` package
3. Use `tmp_path` for test isolation
4. Mock embedding for unit tests

## Acceptance Criteria
- [ ] All 25 tests passing
- [ ] CI/CD pipeline green
- [ ] Tests run in < 30 seconds
- [ ] Test coverage report generated
```

---

### Issue #3: [P0] Unify database location
**Labels:** `bug`, `configuration`, `P0`  
**Assignee:** @Rita

**Body:**
```
## Problem
Database locations are fragmented:
- `~/.memento/memory.db` - Main store
- `~/.openclaw/memory/memory.db` - Auto-memory
- `~/.memento/cache.db` - Embedding cache

## Proposed Solution
Single location: `~/.openclaw/memento/`
```
~/.openclaw/memento/
├── memory.db
├── cache.db
├── config.yaml
├── logs/
└── backups/
```

## Acceptance Criteria
- [ ] Single database location configured
- [ ] All components use same path
- [ ] Migration handles existing data
- [ ] Documentation updated
```

---

### Issue #4: [P0] Fix auto_memory.py import paths
**Labels:** `bug`, `P0`  
**Assignee:** @Bob

**Body:**
```
## Problem
`scripts/auto_memory.py` uses wrong import paths:
```python
sys.path.insert(0, '~/.openclaw/workspace/skills/memory-zvec/scripts')
from store import MemoryStore  # ❌ ImportError
```

## Proposed Solution
```python
sys.path.insert(0, '~/.openclaw/workspace/memento')
from memento import get_store  # ✅ Correct
```

## Acceptance Criteria
- [ ] Auto-memory initializes without errors
- [ ] Uses unified database location
- [ ] Stores interactions successfully
```

---

## P1 - Short Term

### Issue #5: [P1] Implement Rust embedding engine (RFC-001 Phase 2a)
**Labels:** `enhancement`, `performance`, `rust`, `P1`  
**Assignee:** @Rita

**Body:**
```
## Problem
Cold start is ~10 seconds due to Python/PyTorch. Need Rust for <2s cold start.

## Goal
- Rust + ONNX Runtime embedding
- PyO3 Python bindings
- Feature flag: `MEMENTO_RUST=1`
- Target: Cold start 10s → 2s

## Acceptance Criteria
- [ ] Rust embeds text in <100ms
- [ ] Cold start <2s total
- [ ] PyO3 bindings working
- [ ] Fallback to Python if Rust fails
- [ ] CI builds wheels
```

---

### Issue #6: [P1] Create OpenClaw integration hook
**Labels:** `enhancement`, `integration`, `P1`  
**Assignee:** @Brett

**Body:**
```
## Problem
Memento is NOT "fully automatic" - user must manually run `memento remember`.

## Proposed Solution
Create `memento/openclaw_bridge.py`:
```python
class OpenClawMemoryBridge:
    def store_interaction(self, user_msg, agent_response):
        # Auto-store with significance detection
        
    def recall_context(self, query):
        # Return relevant memories
```

## Acceptance Criteria
- [ ] Bridge module created
- [ ] Every conversation auto-stored (if significant)
- [ ] Context automatically recalled
- [ ] No manual intervention required
```

---

### Issue #7: [P1] Package for PyPI
**Labels:** `enhancement`, `packaging`, `P1`  
**Assignee:** @Bob

**Body:**
```
## Problem
Installation requires git clone. Should be `pip install memento-openclaw`.

## Proposed Solution
- Fix package name in pyproject.toml
- Add proper dependencies
- Set up GitHub Actions release workflow
- Test on TestPyPI first

## Acceptance Criteria
- [ ] Package name: `memento-openclaw`
- [ ] Installs with pip
- [ ] CLI works after install
- [ ] Auto-release on git tag
```

---

## P2 - Medium Term

### Issue #8: [P2] Human-like memory features
**Labels:** `enhancement`, `ai`, `P2`

**Body:**
```
## Problem
Current memory is just semantic search. Need human-like features:
- Temporal decay (forget old, remember recent)
- Emotional tagging
- Association webs
- Memory consolidation

## Acceptance Criteria
- [ ] Temporal decay applied to search
- [ ] Context stored and used
- [ ] Associations can be created
- [ ] Consolidation job runs automatically
```

---

### Issue #9: [P2] Raspberry Pi optimization
**Labels:** `enhancement`, `performance`, `arm`, `P2`

**Body:**
```
## Problem
Vision: "Run on Raspberry Pi"
Current: PyTorch too heavy for Pi Zero

## Target Specs (Pi Zero 2 W)
- RAM: <100MB
- Storage: <50MB
- Cold start: <3s

## Solution
- Rust embedding (lightweight)
- Smaller model option (9MB)
- SQLite-only mode (no embeddings)
- ARM wheels on PyPI
```

---

### Issue #10: [P2] Web dashboard
**Labels:** `enhancement`, `ui`, `P2`

**Body:**
```
## Problem
No visual interface for browsing memories.

## Proposed Solution
FastAPI-based web dashboard:
- Browse memories with filters
- Search (semantic + keyword)
- Delete/edit memories
- Visualizations (timeline, tags)

## Usage
```bash
memento server  # Starts web UI on localhost:8000
```
```

---

## How to Create These

### Option 1: GitHub Web Interface
1. Go to https://github.com/Rollersrights/memento/issues
2. Click "New Issue"
3. Copy/paste title and body from above
4. Add labels and assignee
5. Submit

### Option 2: GitHub CLI (if installed)
```bash
gh issue create --title "[P0] Clean up legacy scripts/ folder" \
  --body "..." \
  --label "cleanup,technical-debt,P0" \
  --assignee Bob
```

### Option 3: API (with token)
```bash
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/Rollersrights/memento/issues \
  -d '{
    "title": "[P0] Clean up legacy scripts/ folder",
    "body": "...",
    "labels": ["cleanup", "technical-debt", "P0"],
    "assignees": ["Bob"]
  }'
```
