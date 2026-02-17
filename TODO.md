# TODO - Memento Roadmap (Post-Audit v0.2.0)

## High Priority (Phase 2: Hardening)

- [ ] **Config System:** Replace environment variables with `config.yaml` support.
  - See `scripts/logging_config.py` for inspiration.
  - Need per-user (`~/.memento/config.yaml`) and system (`/etc/memento/config.yaml`) paths.

- [ ] **DB Migrations:** 
  - `store.py` currently auto-creates tables but doesn't handle schema updates.
  - We need a versioning system (e.g., table `schema_version`) to safely upgrade `memory.db`.

- [ ] **Input Validation:**
  - `remember()` accepts any string. Add length limits (e.g., 10k chars) to prevent OOM/DoS.
  - `recall()` needs query sanitization.

## Medium Priority (Phase 3: Polish)

- [ ] **Docker:** Add `Dockerfile` for easy deployment (especially for Federation nodes).
- [ ] **PyPI Package:** Structure as `src/memento` instead of `scripts/` so we can `pip install memento-ai`.
- [ ] **API Docs:** Set up Sphinx to auto-generate docs from our new type hints.

## Low Priority (Experimentation)

- [ ] **Rust Port:**
  - Initial `cargo` project created (`memento_rs`).
  - Blocked on OpenSSL dependency for `fastembed`.
  - Consider pure-Rust ONNX inference (`ort` crate) with pre-downloaded model.

- [ ] **Federation:**
  - Sync logic: `rsync` vs SQLite merge.
  - Identity management (Bob vs Rita).

## Notes for Rita
- **Persistence:** SQLite disk cache is working great (4ms cold boot).
- **Optimization:** ONNX + AVX2 auto-detection is solid.
- **Logging:** Centralized logger is live.
