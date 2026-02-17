# Design Issue: Memory System Lacks Real-Time CLI Visibility

**Status:** Open  
**Priority:** Medium  
**Component:** Auto-Store / Session Watcher

---

## Problem Statement

The current memory system stores conversations automatically, but users have **no visibility** into:
1. What's being stored
2. When it's being stored
3. Whether specific content made it into memory
4. Real-time storage status

### Current Behavior

- Auto-store runs every **3 minutes** (batch processing)
- Storage happens silently in the background
- User must check logs (`~/.openclaw/memory/automemory.log`) or run dashboard to see activity
- No immediate feedback after "remember this" or significant exchanges

### User Impact

> "i cant see all this happening in the cli"  
> "ok, so if i started a new session now would you remember this"

Users are **uncertain** about memory persistence. This undermines trust in the system.

---

## Proposed Solutions

### Option 1: Inline Storage Notifications (Recommended)

Add lightweight CLI feedback when memories are stored:

```
💾 Stored: "implement resilient memory system" (confidence: 0.87)
```

- Shows only for confidence > 0.7 or explicit "remember this"
- One-line, non-intrusive
- Can be disabled via config

### Option 2: Session Summary on Exit

When session ends, show:

```
📊 Session Memory Summary:
   • 12 exchanges analyzed
   • 3 memories stored
   • 2 explicit reminders
```

### Option 3: Real-Time Watcher Logs

Stream watcher activity to a visible panel/file:

```bash
# In separate terminal
$ memento watch
[10:08:12] Scanning session logs...
[10:08:12] Stored: 2 items (confidence: 0.82, 0.91)
[10:08:12] Skipped: 5 items (confidence < 0.4)
```

### Option 4: Echo Mode

Add config flag `auto_store.echo = true` that prints to assistant's response stream:

```
[memory] Stored exchange about "visibility improvements"
```

---

## Technical Considerations

| Approach | Implementation Complexity | User Value | Performance Impact |
|----------|---------------------------|------------|-------------------|
| Inline notifications | Low | High | Minimal |
| Session summary | Medium | Medium | Low |
| Real-time watcher | Medium | High | Moderate |
| Echo mode | Low | Medium | Minimal |

---

## Acceptance Criteria

- [ ] User can see **when** memories are stored without checking logs
- [ ] User can see **what** was stored (brief preview)
- [ ] User can **disable** visibility if desired
- [ ] Feature works across all session types (main, isolated, webchat)

---

## Related Files

- `scripts/session_watcher.py` - Main auto-store logic
- `scripts/conversation_memory.py` - Significance detection
- `scripts/auto_store_hook.py` - Hook integration

---

## Next Steps

1. Discuss preferred approach with stakeholders
2. Prototype inline notification system
3. Add configuration options
4. Test across different session types

---

*Opened: 2026-02-17*  
*Reporter: @rollersrights*
