#!/bin/bash
# Monitor GitHub for Bob's updates
# Run this to check for new PRs, comments, or merges

REPO="rollersrights/memento"
TOKEN="${GITHUB_TOKEN:-}"  # Use environment variable

echo "=== MEMENTO GITHUB MONITOR ==="
echo "Time: $(date)"
echo ""

echo "📋 Open Pull Requests:"
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/$REPO/pulls | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for pr in data:
    print(f\"  #{pr['number']}: {pr['title']}\")
    print(f\"    By: {pr['user']['login']} | Status: {pr['state']}\")
    print(f\"    URL: {pr['html_url']}\")
    print()
" 2>/dev/null || echo "  No open PRs or API error"

echo ""
echo "💬 Recent Issue Comments (last 5):"
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/$REPO/issues/comments?per_page=5 | \
  python3 -c "
import sys, json, datetime
data = json.load(sys.stdin)
for comment in data[:3]:
    user = comment['user']['login']
    body = comment['body'][:80] + '...' if len(comment['body']) > 80 else comment['body']
    print(f\"  {user}: {body}\")
" 2>/dev/null || echo "  No recent comments"

echo ""
echo "🔄 Recent Commits (main branch):"
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/repos/$REPO/commits?sha=main&per_page=3 | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for commit in data:
    msg = commit['commit']['message'].split('\n')[0][:60]
    author = commit['commit']['author']['name']
    print(f\"  {author}: {msg}\")
" 2>/dev/null || echo "  Could not fetch commits"

echo ""
echo "✅ Monitor complete"
