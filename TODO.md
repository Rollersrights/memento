### Infrastructure

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #12 | Add type hints to `store.py` | [x] | @Bob | MemoryStore class |
| #13 | Add type hints to `embed.py` | [x] | @Bob | Done! |
| #14 | Add type hints to `cli.py` | [x] | @Bob | All CLI functions |
| #15 | Add type hints to `search.py` | [x] | @Bob | Search functions |
| #16 | Create `scripts/types.py` | [x] | @Bob | Shared type definitions |
| #17 | Fix bare `except:` clauses | [x] | @Bob | Fixed in core & dashboard |
| #18 | Create `MementoError` class | [x] | @Rita | scripts/exceptions.py |

### Testing

| Ticket | Description | Status | Assignee | Target |
|--------|-------------|--------|----------|--------|
| #19 | Test `embed.py` cache scenarios | [@Rita] | @Rita | 80% coverage - 5/6 tests pass |
| #20 | Test `store.py` edge cases | [ ] | | 70% coverage |
| #21 | Test `search.py` hybrid search | [ ] | | 60% coverage |
| #22 | Test `ingest.py` document loading | [ ] | | 50% coverage |
| #23 | Test `cli.py` argument parsing | [ ] | | 40% coverage |
| #24 | Test concurrent access | [ ] | | Threading safety |

### Reliability

| Ticket | Description | Status | Assignee | Notes |
|--------|-------------|--------|----------|-------|
| #25 | Config system (YAML) | [x] | @Bob | ~/.memento/config.yaml |
| #26 | DB migrations | [x] | @Bob | schema_version table |
| #27 | Input validation | [ ] | @Bob | Length limits, sanitization |
| #28 | Migrate prints to logging | [x] | @Bob | Use logging_config.py |
| #29 | Query timeout option | [ ] | | Prevent hangs |
| #30 | Pagination for results | [ ] | | Limit result sets |