#!/bin/bash
# Memento CI/CD Watcher
# Pulls from GitHub, runs tests, pushes fixes

cd ~/.openclaw/workspace/memento || exit 1

echo "[$(date)] Checking for updates..."

# Fetch latest
git fetch origin main 2>/dev/null

# Check if we're behind
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] New commits found! Pulling..."
    
    # Pull changes
    git pull origin main
    
    echo "[$(date)] Running tests..."
    
    # Run tests
    if ./run_tests.sh > /tmp/memento_test.log 2>&1; then
        echo "[$(date)] ✅ Tests passed"
    else
        echo "[$(date)] ❌ Tests failed! Check /tmp/memento_test.log"
        # Could auto-revert or notify here
    fi
    
    echo "[$(date)] Done"
else
    echo "[$(date)] No updates"
fi
