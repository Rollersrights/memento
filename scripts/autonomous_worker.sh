#!/bin/bash
# Memento Autonomous Worker
# Runs continuously to fix bottlenecks one by one
# Follows proper GitHub workflow

set -e

REPO_DIR="$HOME/.openclaw/workspace/memento"
LOG_FILE="$HOME/.openclaw/memory/autonomous_worker.log"
ISSUE_FILE="$HOME/.openclaw/memory/current_issue.txt"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$REPO_DIR"

# Step 1: Analyze bottlenecks
log "🔍 Analyzing bottlenecks..."
python3 scripts/analyze_bottlenecks.py 2>/dev/null || true

# Step 2: Read current bottlenecks
if [ -f "$HOME/.openclaw/memory/bottlenecks.json" ]; then
    TOP_ISSUE=$(python3 -c "
import json
with open('$HOME/.openclaw/memory/bottlenecks.json') as f:
    bottlenecks = json.load(f)
    if bottlenecks:
        print(bottlenecks[0]['issue'])
" 2>/dev/null)
    
    if [ -n "$TOP_ISSUE" ]; then
        log "🔴 Top bottleneck: $TOP_ISSUE"
    else
        log "✅ No critical bottlenecks found"
        exit 0
    fi
fi

# Step 3: Check if already working on something
if [ -f "$ISSUE_FILE" ]; then
    CURRENT=$(cat "$ISSUE_FILE")
    log "📋 Already working on: $CURRENT"
    
    # Check if branch exists and has uncommitted work
    BRANCH=$(git branch --show-current)
    if [ "$BRANCH" != "main" ]; then
        if [ -n "$(git status --porcelain)" ]; then
            log "💾 Uncommitted changes found, committing..."
            git add -A
            git commit -m "WIP: $CURRENT" || true
            git push origin "$BRANCH" || true
            log "✅ Changes pushed"
        fi
    fi
fi

log "🏁 Autonomous worker cycle complete"
