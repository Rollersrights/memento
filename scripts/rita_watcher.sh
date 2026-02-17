#!/bin/bash
# Rita Chat Watcher - notifies when Rita replies

CHAT_FILE="/home/brett/RITA_CHAT.md"
REMOTE_FILE="bob@192.168.1.155:~/RITA_CHAT.md"
STATE_FILE="/home/brett/.rita_chat_state"
SSH_KEY="/home/brett/.ssh/id_ed25519_bob"

# Sync the file from bob
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_FILE" "$CHAT_FILE.tmp" 2>/dev/null || exit 0

# If no state file exists, create it and exit (first run)
if [ ! -f "$STATE_FILE" ]; then
    wc -l < "$CHAT_FILE.tmp" > "$STATE_FILE"
    mv "$CHAT_FILE.tmp" "$CHAT_FILE"
    exit 0
fi

# Get previous and current line counts
prev_lines=$(cat "$STATE_FILE")
curr_lines=$(wc -l < "$CHAT_FILE.tmp")

# Check if file has grown
if [ "$curr_lines" -gt "$prev_lines" ]; then
    # New content added - check if it's from Rita
    new_content=$(tail -n +$((prev_lines + 1)) "$CHAT_FILE.tmp")
    
    if echo "$new_content" | grep -qE "^## Rita|^Rita →|^From: Rita"; then
        # Rita has replied! Send notification
        echo "$new_content" | head -20 > /tmp/rita_reply.txt
        
        # Use OpenClaw to send notification (via WhatsApp if available)
        echo "📨 Rita replied in RITA_CHAT.md:

$(cat /tmp/rita_reply.txt)" > /tmp/rita_notification.txt
        
        # Update the main file
        mv "$CHAT_FILE.tmp" "$CHAT_FILE"
        
        # Save new state
        echo "$curr_lines" > "$STATE_FILE"
        
        # Try to notify via OpenClaw system event if possible
        # Or just log it for now
        logger "[RitaWatcher] Rita has replied - check RITA_CHAT.md"
        echo "[$(date)] Rita replied - $(echo "$new_content" | head -1)" >> /home/brett/.rita_chat.log
        
        exit 0
    fi
fi

# Update file and state regardless
mv "$CHAT_FILE.tmp" "$CHAT_FILE" 2>/dev/null || true
echo "$curr_lines" > "$STATE_FILE"
