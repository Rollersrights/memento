#!/bin/bash
# Memento CI Manager - Auto-update and Test
# Usage: ./ci_manager.sh

REPO_DIR="/home/brett/.openclaw/workspace/memento"
LOG_FILE="/tmp/memento-ci.log"
TEST_RUNNER="./run_tests.sh"

cd "$REPO_DIR" || exit 1

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "$1"
}

# 1. Fetch
git fetch origin main >/dev/null 2>&1
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "$LOCAL_HASH" == "$REMOTE_HASH" ]; then
    # No updates
    exit 0
fi

log "⬇️ Update detected! Pulling changes..."
log "   $LOCAL_HASH -> $REMOTE_HASH"

# 2. Pull
if ! git pull origin main >> "$LOG_FILE" 2>&1; then
    log "❌ Pull failed! Check git status."
    exit 1
fi

# 3. Run Tests
log "🧪 Running Test Suite..."
if $TEST_RUNNER >> "$LOG_FILE" 2>&1; then
    log "✅ Tests PASSED. Update successful."
    # Optional: Send notification?
else
    log "💥 Tests FAILED after update!"
    log "   Reverting to previous commit ($LOCAL_HASH) for safety..."
    
    # Revert
    git reset --hard "$LOCAL_HASH" >> "$LOG_FILE" 2>&1
    
    log "   Reverted. System state preserved."
    log "   ACTION REQUIRED: Fix the broken build."
    exit 1
fi
