# Security Policy

> Security policy and vulnerability reporting for Memento.

*Last updated: 2026-02-17*

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Memento, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainer directly (see GitHub profile)
3. Allow reasonable time for response before disclosure

## Security Measures

### Input Validation

All user inputs are validated:
- Text length limits (max 100,000 characters)
- Query length limits (max 1,000 characters)
- Tag count limits (max 50 tags)
- Importance range (0.0-1.0)

### SQL Injection Prevention

Memento uses parameterized queries exclusively:
```python
# Safe
conn.execute("SELECT * FROM memories WHERE id = ?", (doc_id,))

# Never done
conn.execute(f"SELECT * FROM memories WHERE id = '{doc_id}'")  # ❌
```

### Path Traversal Prevention

All file paths use `pathlib.Path` for safe resolution:
```python
from pathlib import Path
safe_path = Path(db_path).resolve()
```

### Secrets Handling

- No hardcoded credentials
- Configuration via environment variables or config file
- Config file should have restricted permissions (600)

## Best Practices for Users

1. **Database Permissions:**
   ```bash
   chmod 600 ~/.memento/memory.db
   ```

2. **Backup Encryption:**
   Backups contain your data. Encrypt if sensitive:
   ```bash
   gpg -c memory.db.backup-20240217
   ```

3. **Config File Permissions:**
   ```bash
   chmod 600 ~/.memento/config.yaml
   ```

4. **Shared Memory:**
   If sharing memory across agents, use secure transport:
   ```bash
   # Good: SSH tunnel
   ssh -L  localhost:8080:remote:8080 user@host
   
   # Bad: Unencrypted network share
   ```

## Audit History

| Date | Check | Result |
|------|-------|--------|
| 2026-02-17 | SQL Injection | :white_check_mark: Safe |
| 2026-02-17 | Path Traversal | :white_check_mark: Safe |
| 2026-02-17 | Secrets in Code | :white_check_mark: Clean |
| 2026-02-17 | Input Validation | :white_check_mark: Good |
