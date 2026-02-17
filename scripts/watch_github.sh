#!/bin/bash
# Watch GitHub for new commits on main branch

REPO_DIR="/home/brett/.openclaw/workspace/memento"
LOG_FILE="/tmp/memento-git-watch.log"
STATE_FILE="/home/brett/.memento/last_commit_hash"

mkdir -p $(dirname "$STATE_FILE")

cd "$REPO_DIR" || exit 1

# Get current hash
current_hash=$(git rev-parse HEAD)

# Fetch updates (silent)
git fetch origin main >/dev/null 2>&1

# Get new hash
new_hash=$(git rev-parse origin/main)

# Check change
if [ "$current_hash" != "$new_hash" ]; then
    echo "[$(date)] New commits detected! $current_hash -> $new_hash" >> "$LOG_FILE"
    
    # Get commit message
    msg=$(git log -1 --pretty=%B origin/main)
    author=$(git log -1 --pretty=%an origin/main)
    
    # Notify (via stdout, captured by cron for email/log, or we could hook into OpenClaw)
    echo "🚨 NEW CODE from $author"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$msg"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Run 'cd memento && git pull' to update."
    
    # Update state so we don't spam (optional, but for now we want to know until we pull)
    # echo "$new_hash" > "$STATE_FILE"
    
    # Auto-pull? Maybe safer to just notify.
fi
