#!/bin/bash
# Memento Health Check & Backup Script
# Run periodically to ensure memory system health

LOG_FILE="$HOME/.openclaw/memory/health.log"
DB_FILE="$HOME/.openclaw/memory/memory.db"
BACKUP_DIR="$HOME/.openclaw/memory/backups"
GITHUB_REPO="rollersrights/memento"

# Ensure directories exist
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Memento Health Check Starting" >> "$LOG_FILE"

# Check if database exists and is readable
if [ ! -f "$DB_FILE" ]; then
    echo "[$(date)] ❌ CRITICAL: Database not found at $DB_FILE" >> "$LOG_FILE"
    
    # Try rollback
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/memory_*.db 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" "$DB_FILE"
        echo "[$(date)] ✅ Rollback from $LATEST_BACKUP completed" >> "$LOG_FILE"
    else
        echo "[$(date)] ❌ No backup available for rollback" >> "$LOG_FILE"
        # Create GitHub issue (would need API key)
        echo "[$(date)] 📝 GitHub Issue should be created: Database missing" >> "$LOG_FILE"
    fi
    exit 1
fi

# Check database integrity
if ! sqlite3 "$DB_FILE" "PRAGMA integrity_check;" | grep -q "ok"; then
    echo "[$(date)] ❌ CRITICAL: Database integrity check failed" >> "$LOG_FILE"
    
    # Rollback
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/memory_*.db 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" "$DB_FILE"
        echo "[$(date)] ✅ Rollback completed" >> "$LOG_FILE"
    fi
    exit 1
fi

# Create daily backup
BACKUP_FILE="$BACKUP_DIR/memory_$(date +%Y%m%d_%H%M%S).db"
cp "$DB_FILE" "$BACKUP_FILE"
echo "[$(date)] ✅ Backup created: $BACKUP_FILE" >> "$LOG_FILE"

# Clean old backups (keep last 7)
ls -t "$BACKUP_DIR"/memory_*.db | tail -n +8 | xargs -r rm

# Get stats
VECTOR_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM memories;" 2>/dev/null || echo "0")
DB_SIZE=$(du -h "$DB_FILE" | cut -f1)

echo "[$(date)] ℹ️ Stats: $VECTOR_COUNT vectors, $DB_SIZE size" >> "$LOG_FILE"

echo "[$(date)] ✅ Health check passed" >> "$LOG_FILE"
exit 0
