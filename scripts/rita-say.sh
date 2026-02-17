#!/bin/bash
# Send message to Rita - syncs to bob immediately

MESSAGE="$*"
SSH_KEY="/home/brett/.ssh/id_ed25519_bob"
REMOTE_USER="bob"
REMOTE_HOST="192.168.1.155"
CHAT_FILE="/home/brett/RITA_CHAT.md"
REMOTE_FILE="~/RITA_CHAT.md"

if [ -z "$MESSAGE" ]; then
    echo "Usage: rita-say <message>"
    echo "Example: rita-say Hey Rita, what do you think about the benchmark?"
    exit 1
fi

# Add timestamp and my message to local file
echo "" >> "$CHAT_FILE"
echo "## Bob → Rita ($(date '+%H:%M %Z'))" >> "$CHAT_FILE"
echo "" >> "$CHAT_FILE"
echo "$MESSAGE" >> "$CHAT_FILE"
echo "" >> "$CHAT_FILE"
echo "---" >> "$CHAT_FILE"

# Sync to bob
if scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$CHAT_FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_FILE" >/dev/null 2>&1; then
    echo "✅ Sent to Rita: $MESSAGE"
else
    echo "❌ Failed to sync to Rita"
    exit 1
fi
