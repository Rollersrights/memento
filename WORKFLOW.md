# GitHub Workflow for Memento

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
- [ ] Code quality
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Performance acceptable

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

## ✅ What TO do

- ✅ Create issues before starting work
- ✅ Use feature branches
- ✅ Write descriptive commit messages
- ✅ Reference issues in commits/PRs
- ✅ Request reviews
- ✅ Respond to feedback promptly
- ✅ Keep PRs focused and small

## 🔐 Branch Protection

`main` branch is protected:
- Requires PR to merge
- Requires 1 review approval
- CI tests must pass
- No force pushes

## 📝 Commit Message Examples

**Good:**
```
Issue #17: Fix bare except clauses in dashboard.py

- Replaced 4 bare 'except:' with 'except Exception'
- Added descriptive comments
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

## 👥 Roles

**@rollersrights (Rita):**
- Performance optimizations
- Cross-platform compatibility
- Infrastructure

**@Bob:**
- Code quality (types, tests)
- CLI/UX improvements
- Documentation
- Rust integration

## 📋 Checklist for PRs

- [ ] Issue created and linked
- [ ] Branch created from latest main
- [ ] Changes are focused and atomic
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] CI passes
- [ ] Review requested
- [ ] Feedback addressed
- [ ] Squash merged to main

---

*This workflow ensures code quality and collaboration.*
