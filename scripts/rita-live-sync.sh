#!/bin/bash
# Real-time two-way sync between Bob and Rita
# Run this in background for live chat

LOCAL_FILE="/home/brett/RITA_CHAT.md"
REMOTE_FILE="bob@192.168.1.155:~/RITA_CHAT.md"
SSH_KEY="/home/brett/.ssh/id_ed25519_bob"
STATE_FILE="/home/brett/.rita_sync_state"
SYNC_INTERVAL=10  # seconds

echo "🔄 Starting real-time sync with Rita on bob..."
echo "   Local: $LOCAL_FILE"
echo "   Remote: $REMOTE_FILE"
echo "   Interval: ${SYNC_INTERVAL}s"
echo "   Press Ctrl+C to stop"
echo ""

# Create files if they don't exist
touch "$LOCAL_FILE"
[ ! -f "$STATE_FILE" ] && echo "0" > "$STATE_FILE"

sync_to_remote() {
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        "$LOCAL_FILE" "$REMOTE_FILE" >/dev/null 2>&1
}

sync_from_remote() {
    local tmp_file="${LOCAL_FILE}.remote"
    if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        "$REMOTE_FILE" "$tmp_file" >/dev/null 2>&1; then
        
        # Check if remote file has new content
        local local_lines=$(wc -l < "$LOCAL_FILE" 2>/dev/null || echo 0)
        local remote_lines=$(wc -l < "$tmp_file" 2>/dev/null || echo 0)
        
        if [ "$remote_lines" -gt "$local_lines" ]; then
            # Rita added something - show it
            local new_lines=$((remote_lines - local_lines))
            echo ""
            echo "📨 RITA REPLIED ($new_lines lines):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            tail -n "$new_lines" "$tmp_file" | grep -v "^## Bob" | head -20
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            # Update local file
            cp "$tmp_file" "$LOCAL_FILE"
        fi
        
        rm -f "$tmp_file"
    fi
}

# Main loop
cleanup() {
    echo ""
    echo "👋 Sync stopped"
    exit 0
}
trap cleanup INT TERM

while true; do
    # Sync both ways
    sync_from_remote
    sleep $SYNC_INTERVAL
done
