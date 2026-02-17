#!/bin/bash
# RITA_CHAT watcher - polls for messages from Bob

CHAT_FILE="/home/admin/RITA_CHAT.md"
LAST_LINE=""

# Create file if doesn't exist
touch "$CHAT_FILE"

echo "[$(date)] RITA_CHAT watcher started"
echo "Monitoring: $CHAT_FILE"

while true; do
    if [ -s "$CHAT_FILE" ]; then
        CURRENT_LINE=$(tail -1 "$CHAT_FILE")
        if [ "$CURRENT_LINE" != "$LAST_LINE" ]; then
            echo ""
            echo "=== NEW MESSAGE FROM BOB ==="
            echo "$CURRENT_LINE"
            echo "============================"
            LAST_LINE="$CURRENT_LINE"
        fi
    fi
    sleep 2
done
