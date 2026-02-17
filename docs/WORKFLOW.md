# Workflow

> GitHub workflow and development process for Memento.

*Last updated: 2026-02-17*

---

## 🔄 Development Process

We use proper GitHub collaboration: **Issues → Branches → PRs → Reviews → Merge**

### 1. Create an Issue

All work starts with a GitHub issue:
- Bug reports
- Feature requests  
- RFC implementation tasks
- Refactoring work

Issue template: `[Area] Brief description`

### 2. Create a Feature Branch

```bash
# From main, create feature branch
git checkout main
git pull origin main
git checkout -b feature/issue-XX-short-name

# Example:
git checkout -b feature/issue-2-engine-abc
```

**Branch naming:**
- `feature/issue-XX-description` - New features
- `fix/issue-XX-description` - Bug fixes
- `docs/issue-XX-description` - Documentation
- `rfc-XXX-phase-N` - RFC implementation

### 3. Make Changes

Work on your branch:
```bash
# Edit files
git add .
git commit -m "Issue #XX: Description of change

- Detail 1
- Detail 2

Fixes #XX"
```

**Commit message format:**
```
Issue #XX: Brief summary

- What changed
- Why it changed
- Any breaking changes

Fixes #XX
```

### 4. Push and Create PR

```bash
git push origin feature/issue-XX-short-name
```

Then create PR via GitHub:
- Use PR template
- Link to issue: "Fixes #XX"
- Request review from @rollersrights or @Bob
- Ensure CI passes

### 5. Code Review

**Reviewers check:**
- [ ] Code quality (type hints, docstrings)
- [ ] Tests pass (including new tests)
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Performance acceptable
- [ ] CI passes

**Address feedback:**
```bash
# Make requested changes
git add .
git commit -m "Address review feedback: description"
git push origin feature/issue-XX-short-name
```

### 6. Merge

After approval:
- Use "Squash and merge" for clean history
- Delete feature branch after merge
- Close linked issue

## 🚫 What NOT to do

- ❌ Push directly to `main`
- ❌ Merge without review
- ❌ Delete branches before PR merge
- ❌ Work on multiple features in one branch
- ❌ Skip type hints on public APIs
- ❌ Skip tests for new features

## ✅ What TO do

- ✅ Create issues before starting work
- ✅ Use feature branches
- ✅ Write descriptive commit messages
- ✅ Reference issues in commits/PRs
- ✅ Request reviews
- ✅ Respond to feedback promptly
- ✅ Keep PRs focused and small
- ✅ Add type hints to all functions
- ✅ Update CHANGELOG.md

## 🔐 Branch Protection

`main` branch is protected:
- Requires PR to merge
- Requires 1 review approval
- CI tests must pass
- No force pushes
- Up to date with base branch

## 📝 Commit Message Examples

**Good:**
```
Issue #17: Fix bare except clauses in dashboard.py

- Replaced 4 bare 'except:' with 'except Exception'
- Added logging for caught exceptions
- Added test coverage for error paths
- No functional changes

Fixes #17
```

**Bad:**
```
fix stuff
```

## 🏷️ Labels

- `bug` - Something is broken
- `enhancement` - New feature
- `documentation` - Docs only
- `rfc-XXX` - Related to RFC
- `phase-N` - Implementation phase
- `performance` - Speed improvements
- `refactoring` - Code restructuring
- `good first issue` - Beginner-friendly
- `help wanted` - Community contribution welcome

## 👥 Roles

**@rollersrights (Rita):**
- Performance optimizations
- Cross-platform compatibility
- Infrastructure
- Rust integration

**Bob:**
- Code quality (types, tests)
- CLI/UX improvements
- Documentation
- CI/CD

**Brett:**
- Architecture decisions
- Integration
- Deployment

## 📋 Checklist for PRs

- [ ] Issue created and linked
- [ ] Branch created from latest main
- [ ] Changes are focused and atomic
- [ ] Type hints added/updated
- [ ] Tests added/updated
- [ ] Documentation updated (README, docstrings)
- [ ] CHANGELOG.md updated
- [ ] CI passes
- [ ] Review requested
- [ ] Feedback addressed
- [ ] Squash merged to main

## 🧪 CI Requirements

All PRs must pass:
- Python 3.8, 3.9, 3.10, 3.11, 3.12 tests
- flake8 linting
- pytest test suite
- CLI smoke tests

---

*This workflow ensures code quality and collaboration.*
