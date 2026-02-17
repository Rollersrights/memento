#!/bin/bash
# Memento Git Branch Cleanup Script
# Run this to tidy up merged and stale branches

echo "=== MEMENTO BRANCH CLEANUP PLAN ==="
echo ""

cd /home/brett/.openclaw/workspace/memento

# First, commit or stash current changes on main
echo "⚠️  IMPORTANT: You have uncommitted changes on main"
echo "   - memento/store.py has rate limiting and sanitization code"
echo "   - 6 other untracked files"
echo ""

echo "Step 1: Commit current work on main"
echo "-------"
echo "  git add memento/store.py"
echo "  git commit -m 'feat: Add rate limiting and input sanitization (security)'"
echo ""

echo "Step 2: Delete LOCAL branches that are already merged"
echo "-------"

# These branches have no unique commits (already merged into main)
STALE_LOCAL=(
  "feature/issue-13-cold-start"
  "feature/issue-14-query-timeout"
  "feature/issue-14-recovery"
  "feature/issue-15-import-path-fix"
  "feature/issue-19-model-ram-idle"
  "feature/issue-20-cache-warming"
)

for branch in "${STALE_LOCAL[@]}"; do
  echo "  git branch -D $branch"
done

echo ""
echo "Step 3: Handle branches with UNMERGED work"
echo "-------"
echo ""
echo "🔍 feature/issue-14-session-recovery (LOCAL)"
echo "   Has session recovery script - NEEDS DECISION"
echo "   View: git log main..feature/issue-14-session-recovery"
echo "   Options:"
echo "     a) Merge it: git merge feature/issue-14-session-recovery"
echo "     b) Cherry-pick: git cherry-pick ff66741"
echo "     c) Discard: git branch -D feature/issue-14-session-recovery"
echo ""

echo "🔍 feature/issue-8-package-restructure (LOCAL + REMOTE)"
echo "   Has package restructure work - DIVERGED from main"
echo "   Main has: 06e0831 'Complete package restructure'"
echo "   Branch has: 48213be 'Package restructure - scripts/ → memento/'"
echo "   Action: Compare and potentially discard local branch"
echo "   git diff main..feature/issue-8-package-restructure"
echo ""

echo "🔍 feature/issue-11-mission-statement (REMOTE)"
echo "   Has echo notifications commit: 2148c0c"
echo "   Action: Check if needed, then delete remote branch"
echo "   git log main..origin/feature/issue-11-mission-statement"
echo ""

echo "🔍 feature/phase1-modularization (LOCAL)"
echo "   Has merge commit only (5bd919c) - likely stale"
echo "   Action: Delete after confirming"
echo ""

echo "🔍 temp-recovery (LOCAL)"
echo "   No unique commits - likely temporary"
echo "   Action: Delete"
echo ""

echo "Step 4: Delete REMOTE branches that are stale"
echo "-------"

STALE_REMOTE=(
  "feature/issue-13-cold-start"
  "feature/issue-14-query-timeout"
  "feature/issue-14-recovery"
  "feature/issue-15-import-path-fix"
  "feature/issue-19-model-ram-idle"
  "feature/issue-20-cache-warming"
  "feature/phase1-modularization"
  "feature/resilient-memory"
  "feature/ticket-2-engine-abc"
  "fix/test-failures"
)

for branch in "${STALE_REMOTE[@]}"; do
  echo "  git push origin --delete $branch"
done

echo ""
echo "Step 5: Prune stale remote tracking branches"
echo "-------"
echo "  git remote prune origin"
echo ""

echo "=== RECOMMENDED ACTIONS ==="
echo ""
echo "SAFE TO DELETE NOW (already merged):"
echo "  git branch -D feature/issue-13-cold-start"
echo "  git branch -D feature/issue-14-query-timeout"
echo "  git branch -D feature/issue-14-recovery"
echo "  git branch -D feature/issue-15-import-path-fix"
echo "  git branch -D feature/issue-19-model-ram-idle"
echo "  git branch -D feature/issue-20-cache-warming"
echo "  git branch -D feature/phase1-modularization"
echo "  git branch -D temp-recovery"
echo ""
echo "NEED DECISION:"
echo "  feature/issue-14-session-recovery - has unmerged session recovery work"
echo "  feature/issue-8-package-restructure - diverged from main's version"
echo "  origin/feature/issue-11-mission-statement - remote has echo notifications"
echo "  origin/feature/issue-8-package-restructure - remote has different restructure"
echo ""
