---
title: "[P0] Clean up legacy scripts/ folder - remove duplicate/outdated code"
labels: ["cleanup", "technical-debt", "P0"]
assignees: ["Bob"]
---

## Problem
The codebase has 12,610 lines of Python but should be "small and beautiful". The `scripts/` folder contains legacy, duplicate, and outdated code that:
- Duplicates functionality in `memento/` package
- Causes import path confusion
- Breaks tests that reference wrong paths
- Increases maintenance burden

## Current Structure Issues
```
scripts/              # Legacy, should be removed
  ├── cli.py         # Old CLI, memento/cli.py replaces this
  ├── store.py       # Old store, memento/store.py replaces this
  ├── embed.py       # Old embed, memento/embed.py replaces this
  └── ...

memento/             # Current package (correct)
  ├── cli.py
  ├── store.py
  ├── embed.py
  └── ...

scripts.backup.*/    # Multiple backup copies
```

## Proposed Solution

### Step 1: Archive Legacy Code
```bash
# Create archive with date stamp
mkdir -p archive/legacy-scripts-$(date +%Y%m%d)
cp -r scripts/* archive/legacy-scripts-$(date +%Y%m%d)/
git add archive/
git commit -m "archive: backup legacy scripts before removal"
```

### Step 2: Remove Legacy Folders
```bash
rm -rf scripts/
rm -rf scripts.backup.*/
git rm -r scripts/
git commit -m "cleanup: remove legacy scripts/ folder"
```

### Step 3: Fix Import Paths
Update any files still importing from `scripts.` to use `memento.`:
- `tests/test_*.py`
- Any documentation examples
- `auto_memory.py`

## Acceptance Criteria
- [ ] `scripts/` folder removed from repo
- [ ] `scripts.backup.*/` folders removed
- [ ] All imports use `memento.` package only
- [ ] Tests still pass (or fail for other reasons)
- [ ] Archive folder created for reference

## Why This Matters
- Reduces confusion for developers
- Single source of truth
- Smaller, cleaner codebase
- Fixes test path issues

## Related
- #2 (Fix failing test suite)
- #4 (Fix auto-memory import paths)
