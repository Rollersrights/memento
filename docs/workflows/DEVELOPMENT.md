# Memento Development Workflow

> **Purpose:** Document the canonical workflow for maintaining Memento. All contributors (human and agent) must follow this process.

## Overview

```
GitHub Issues → Pick Task → Develop → Test → PR → Review → Merge
```

---

## Step-by-Step Workflow

### 1. Check GitHub Issues

**Before starting any work:**

```bash
# List open issues by priority
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/Rollersrights/memento/issues?state=open&labels=P0" | \
  jq -r '.[] | "#\(.number): \(.title)"'
```

**Priority Order:**
1. P0 (Critical) - Fix immediately
2. P1 (Important) - Next in queue
3. P2 (Nice to have) - When P0/P1 clear

**Rules:**
- Never work on P2 while P0 exists
- Comment on issue before starting: "Taking this"
- Assign yourself to the issue

---

### 2. Create Feature Branch

```bash
# From main, always
git checkout main
git pull origin main

# Create branch with issue reference
git checkout -b "feature/issue-XX-short-description"
# Example: git checkout -b "feature/issue-22-rust-embedding"
```

---

### 3. Develop

**Standards:**
- Type hints: 100% coverage
- Docstrings: All public functions
- Tests: Write before or with code
- No hardcoded paths - use config

**Before committing:**
```bash
# Run quick checks
python3 -m py_compile memento/*.py
find memento -name "*.py" | xargs python3 -m py_compile

# Test the specific change
python3 -c "from memento.changed_module import changed_function; changed_function()"
```

---

### 4. Test Locally

**Required Tests:**

```bash
# 1. Unit tests
python3 -m pytest tests/ -v

# 2. Integration test
python3 -c "
from memento.store import get_store
from memento.embed import embed

# Test store
s = get_store()
id = s.remember('test', importance=0.5)
assert len(s.recall('test')) > 0

# Test embed
v = embed('hello')
assert len(v) == 384

print('✅ Integration tests passed')
"

# 3. CLI test
memento stats
memento remember "workflow test" --importance 0.5
memento recall "workflow"
```

**If tests fail:**
1. Fix the code, not the test (unless test is wrong)
2. Update test if behavior intentionally changed
3. Document breaking changes in PR

---

### 5. Update Test Suite

**Add tests for new functionality:**

```python
# tests/test_new_feature.py
def test_new_feature():
    """Test description - what and why."""
    # Setup
    store = get_store()
    
    # Execute
    result = store.new_method()
    
    # Assert
    assert result is not None
    assert result.status == 'success'
```

**Run full suite:**
```bash
python3 -m pytest tests/ --cov=memento --cov-report=term-missing
```

**Coverage target:** 80%+ (current: ~40% - improving)

---

### 6. Commit

**Commit message format:**
```
type: Brief description (#issue-number)

- Detailed change 1
- Detailed change 2
- Breaking change note (if applicable)

Fixes #XX
Related #YY
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `perf:` Performance improvement
- `refactor:` Code restructuring
- `test:` Test additions/changes
- `docs:` Documentation
- `cleanup:` Removal of dead code

**Example:**
```
feat: Implement Rust embedding engine (#22)

- Add onnxruntime support via ort crate
- Implement mean pooling and normalization
- PyO3 bindings for Python integration
- 10s → 2s cold start improvement

Fixes #22
Related #21
```

---

### 7. Push and Create PR

```bash
git push -u origin feature/issue-XX-description
```

**PR Template:**
```markdown
## Description
Brief description of changes

## Related Issue
Fixes #XX

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Breaking change

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing done

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings

## Benchmarks (if applicable)
Before: X seconds
After: Y seconds
Improvement: Z%
```

---

### 8. Review Process

**Reviewer Checklist:**
- [ ] Code logic correct
- [ ] Tests cover new code
- [ ] No performance regressions
- [ ] Documentation updated
- [ ] No security issues

**Approval Requirements:**
- At least 1 review for P1/P2
- At least 2 reviews for P0
- All CI checks pass
- No unresolved conversations

---

### 9. Merge

**Squash and merge** for clean history:
```bash
# GitHub UI: Squash and merge
# Or locally:
git checkout main
git merge --squash feature/issue-XX-description
git commit -m "feat: Description (#XX)"
git push origin main
```

**After merge:**
- Delete branch
- Close issue (if not auto-closed)
- Update project board

---

## Research Integration

### Adding Research Findings

1. **Create research document:**
   ```bash
   RESEARCH/papers/YYYY-MM-DD-topic.md
   RESEARCH/experiments/YYYY-MM-DD-experiment.md
   RESEARCH/decisions/YYYY-MM-DD-decision.md
   ```

2. **Update DISCUSSION.md:**
   ```markdown
   ### [YYYY-MM-DD] [RESEARCH] Topic - Name
   
   **Findings:** Summary
   
   **Recommendation:** Action item
   
   **Related:** #issue, RESEARCH/path/to/paper.md
   
   **Status:** [COMPLETED]
   ```

3. **Create GitHub issue if actionable:**
   - Use research to justify priority
   - Link to research document

---

## Weekly Review Process

**Every Monday:**

1. **Review open issues:**
   - Close stale issues
   - Re-prioritize if needed
   - Check for blockers

2. **Update DISCUSSION.md:**
   - Mark completed items
   - Add new research findings
   - Archive old discussions

3. **Check roadmap alignment:**
   - Are we on track for milestones?
   - Update ROADMAP.md if dates slip

4. **Review new research:**
   - Check for relevant papers
   - Update RESEARCH/papers/
   - Create issues for promising ideas

---

## Emergency Hotfix Process

**For critical bugs in production:**

1. **Create hotfix branch from main:**
   ```bash
   git checkout -b hotfix/critical-description
   ```

2. **Fix with minimal changes**

3. **Fast-track review:**
   - Ping reviewers immediately
   - Skip non-critical checks

4. **Merge and tag:**
   ```bash
   git tag -a vX.Y.Z -m "Hotfix: description"
   git push origin vX.Y.Z
   ```

5. **Post-mortem:**
   - Document what went wrong
   - Add regression test
   - Update process if needed

---

## Communication Guidelines

### GitHub Issues
- **Title:** Clear, actionable
- **Description:** Context + acceptance criteria
- **Labels:** Priority + type + component
- **Assignee:** Always assigned

### Pull Requests
- **Small:** <500 lines changed preferred
- **Focused:** One logical change per PR
- **Tested:** All tests pass
- **Documented:** PR description complete

### Discussion (DISCUSSION.md)
- **Concise:** Bullet points preferred
- **Referenced:** Link to issues/papers
- **Dated:** Always include date
- **Signed:** Who made the entry

---

## Tooling

### Required Tools
```bash
# Python
git clone https://github.com/Rollersrights/memento.git
cd memento
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Rust (for core development)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup target add wasm32-unknown-unknown  # For WASM builds

# Testing
pip install pytest pytest-cov
```

### Pre-commit Hooks (Recommended)
```bash
pip install pre-commit
pre-commit install

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

---

## Metrics

**Track these weekly:**
- Open P0 issues: Target 0
- Open P1 issues: Target <5
- Test pass rate: Target >90%
- Code coverage: Target >80%
- Cold start time: Target <2s
- LOC: Track complexity growth

---

## Quick Reference Card

```
START WORK:
  1. Check GitHub issues (P0 first)
  2. git checkout -b feature/issue-XX-desc
  3. Code + test locally
  4. Commit with issue ref
  5. Push + create PR
  6. Request review
  7. Merge on approval

RESEARCH:
  1. Document in RESEARCH/papers/
  2. Add to DISCUSSION.md
  3. Create issue if actionable

EMERGENCY:
  1. hotfix/ branch
  2. Minimal fix
  3. Fast review
  4. Merge + tag
```

---

*This workflow is living documentation. Propose changes via PR.*
*Last updated: 2026-02-17*
*Version: 1.0*
