---
title: "[P2] Human-like memory features - temporal decay, associations, consolidation"
labels: ["enhancement", "ai", "P2"]
assignees: []
---

## Problem
Current memory is just semantic search. Vision requires "operates like real human memory."

Human memory characteristics missing:
- **Temporal decay** - forget old, remember recent
- **Emotional tagging** - stressful/important = stronger memory
- **Association webs** - "this reminds me of that"
- **Consolidation** - summarize old memories over time
- **Context-dependent recall** - where/when matters

## Proposed Features

### 1. Temporal Decay
```python
# Memories lose importance over time
class TemporalDecay:
    def calculate_current_importance(
        self,
        original_importance: float,
        age_days: float
    ) -> float:
        # Ebbinghaus forgetting curve
        decay_rate = 0.1  # Configurable
        return original_importance * math.exp(-decay_rate * age_days)
```

### 2. Emotional/Contextual Tagging
```python
store.remember(
    text="Production server crashed!",
    importance=0.95,
    tags=["urgent", "stressful", "production"],
    context={
        "stress_level": 0.9,
        "time_of_day": "3am",
        "location": "home"
    }
)
```

### 3. Memory Associations
```python
class MemoryAssociations:
    def create_association(self, memory_id_a: str, memory_id_b: str):
        """Link related memories."""
        
    def recall_with_associations(self, query: str) -> List[Memory]:
        """Get results plus associated memories."""
        primary = self.store.recall(query)
        associated = []
        for mem in primary:
            associated.extend(self.get_associated(mem.id))
        return primary + associated
```

### 4. Memory Consolidation (Sleep Mode)
```python
class MemoryConsolidator:
    """
    Periodically summarize old memories.
    Like human sleep - consolidates short-term to long-term.
    """
    
    def consolidate(self, older_than_days: int = 30):
        """
        Find old memories, summarize them, store summary,
        optionally archive original details.
        """
        old_memories = self.store.get_old_memories(
            older_than_days=older_than_days
        )
        
        # Group by topic
        clusters = self._cluster_memories(old_memories)
        
        for cluster in clusters:
            summary = self._summarize_cluster(cluster)
            self.store.remember(
                text=summary,
                importance=cluster.avg_importance,
                tags=["consolidated"] + cluster.tags,
                source="consolidation"
            )
```

### 5. Context-Dependent Recall
```python
class ContextualRecall:
    def recall(
        self,
        query: str,
        current_context: Dict  # time, location, recent topics
    ):
        # Boost memories from similar contexts
        base_results = self.store.recall(query)
        
        for result in base_results:
            context_similarity = self._calculate_context_similarity(
                result.context,
                current_context
            )
            result.score *= (1 + context_similarity)
        
        return sorted(base_results, key=lambda r: r.score, reverse=True)
```

## Database Schema Changes
```sql
-- Add context column
ALTER TABLE memories ADD COLUMN context_json TEXT;

-- Associations table
CREATE TABLE memory_associations (
    memory_a_id TEXT,
    memory_b_id TEXT,
    strength REAL DEFAULT 0.5,
    created_at INTEGER,
    FOREIGN KEY (memory_a_id) REFERENCES memories(id),
    FOREIGN KEY (memory_b_id) REFERENCES memories(id)
);

-- Consolidation tracking
CREATE TABLE consolidation_log (
    id INTEGER PRIMARY KEY,
    original_ids TEXT,  -- JSON array
    summary_id TEXT,
    consolidated_at INTEGER
);
```

## Implementation Phases

### Phase 1: Temporal Decay
- Add decay calculation to search
- Configurable decay rate
- Visual indicator of memory age

### Phase 2: Contextual Tagging
- Store context with memories
- Context-based boosting

### Phase 3: Associations
- Manual association creation
- Automatic association detection (similar embeddings)

### Phase 4: Consolidation
- Background consolidation job
- Summary generation (using LLM)
- Archive old detailed memories

## Acceptance Criteria
- [ ] Temporal decay applied to search results
- [ ] Context stored and used for recall
- [ ] Associations can be created and queried
- [ ] Consolidation job runs automatically
- [ ] Feels more "human" in recall quality

## Related
- Vision: "human-like memory"
- #6 (OpenClaw integration - provides context)
