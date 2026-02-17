# Contributing to Memento

Thank you for your interest in contributing! Memento is a collaborative project between AI agents and humans.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/rollersrights/memento.git
cd memento

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
./run_tests.sh
```

## Code Style

- **Python:** Follow PEP 8
- **Line length:** 100 characters (enforced by flake8)
- **Formatter:** Black (run `black .` before committing)
- **Linter:** flake8 (run `flake8 .` before committing)
- **Type hints:** Required for all public APIs

## Type Hints

All functions must have type annotations:

```python
# Good
def recall(
    self,
    query: str,
    collection: Optional[str] = None,
    topk: int = 5
) -> List[Dict[str, Any]]:
    ...

# Bad (missing types)
def recall(self, query, collection=None, topk=5):
    ...
```

## Testing

All contributions should include tests:

```bash
# Add tests to tests/
# Run the test suite
./run_tests.sh

# Or with pytest directly
pytest tests/ -v
```

## Commit Messages

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `perf:` Performance improvement
- `refactor:` Code restructuring
- `test:` Adding tests
- `types:` Type hint additions/changes

Example: `feat: add query timeout option`

Full format:
```
Issue #XX: Brief summary

- What changed
- Why it changed
- Any breaking changes

Fixes #XX
```

## Pull Request Process

1. Create a GitHub issue first
2. Fork the repository
3. Create a feature branch (`git checkout -b feature/issue-XX-short-name`)
4. Make your changes
5. Run tests and linting
6. Update CHANGELOG.md
7. Commit with clear messages
8. Push to your fork
9. Open a Pull Request

### PR Checklist

- [ ] Issue created and linked
- [ ] Type hints added/updated
- [ ] Tests added/updated
- [ ] Documentation updated (README, API docs)
- [ ] CHANGELOG.md updated
- [ ] CI passes

## Areas Needing Help

See `TODO.md` and `AUDIT.md` for current gaps. Priority areas:

- 🔴 **Tests** - Increasing coverage to 80%
- 🟡 **Rust Integration** - PyO3 bindings, ONNX engine
- 🟡 **Documentation** - More examples, tutorials
- 🟢 **Performance** - Benchmarks, optimizations

## Project Structure

```
memento/
├── memento/           # Main package
│   ├── __init__.py    # Public API exports
│   ├── store.py       # MemoryStore class
│   ├── embed.py       # Embedding engine
│   ├── search.py      # Vector search
│   ├── cli.py         # Command line interface
│   ├── models.py      # Data models
│   ├── exceptions.py  # Custom exceptions
│   ├── config.py      # Configuration
│   └── migrations.py  # DB migrations
├── scripts/           # Legacy scripts
├── tests/             # Test suite
├── memento_rs/        # Rust implementation
└── docs/              # Documentation
```

## Documentation

When adding features:

1. Update docstrings (Google style):
```python
def remember(self, text: str, importance: float = 0.5) -> str:
    """Store a memory.
    
    Args:
        text: The text to remember
        importance: 0.0-1.0 relevance score
        
    Returns:
        Document ID
        
    Raises:
        ValidationError: If input is invalid
    """
```

2. Update `API.md` with new functions/classes
3. Update `README.md` if user-facing
4. Update `CHANGELOG.md`

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.X.X`
4. Push tag: `git push origin v0.X.X`
5. CI will build and publish to PyPI (when configured)

## Code of Conduct

Be respectful, constructive, and collaborative.

### Our Standards

- Welcome newcomers
- Assume good intent
- Focus on the code, not the person
- Accept constructive criticism gracefully
- Show empathy towards others

### Enforcement

Violations can be reported to the maintainers.

## Questions?

- Open an issue
- Check existing documentation
- Review closed issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
