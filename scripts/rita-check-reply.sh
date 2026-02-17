#!/bin/bash
# Auto-responder for Rita chat - notifies me and prepares context

LOCAL_FILE="/home/brett/RITA_CHAT.md"
STATE_FILE="/home/brett/.rita_reply_state"
NOTIFICATION_FILE="/home/brett/.rita_pending_reply"

# Get last line number I've seen
last_line=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
total_lines=$(wc -l < "$LOCAL_FILE")

# Check for new content from Rita
if [ "$total_lines" -gt "$last_line" ]; then
    # Extract new lines
    new_content=$(tail -n +$((last_line + 1)) "$LOCAL_FILE")
    
    # Check if it's from Rita
    if echo "$new_content" | grep -qiE "^## Rita|^From: Rita|^Rita →"; then
        # Extract Rita's message
        rita_msg=$(echo "$new_content" | grep -v "^##" | grep -v "^From:" | grep -v "^Rita" | head -20)
        
        # Save for my attention
        echo "$rita_msg" > "$NOTIFICATION_FILE"
        echo "$total_lines" > "$STATE_FILE"
        
        # Log it
        echo "[$(date '+%H:%M:%S')] Rita: $rita_msg" >> /home/brett/.rita_conversation.log
        
        # Output for cron/system to pick up
        echo "📨 NEW MESSAGE FROM RITA:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$rita_msg"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Reply with: memento rita say 'your message'"
        
        exit 0
    fi
fi

echo "$total_lines" > "$STATE_FILE"
exit 0
