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
pip install -e ".[dev,fast]"

# Run tests
./run_tests.sh
```

## Code Style

- **Python:** Follow PEP 8
- **Line length:** 100 characters
- **Formatter:** Black (run `black .` before committing)
- **Linter:** flake8 (run `flake8 .` before committing)

## Testing

All contributions should include tests:

```bash
# Add tests to tests/
# Run the test suite
./run_tests.sh
```

## Commit Messages

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `perf:` Performance improvement
- `refactor:` Code restructuring
- `test:` Adding tests

Example: `feat: add query timeout option`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Areas Needing Help

See `AUDIT.md` for current gaps. Priority areas:

- 🔴 **Type hints** - Adding type annotations
- 🔴 **Tests** - Increasing coverage
- 🟡 **Documentation** - API docs, examples
- 🟡 **Performance** - Benchmarks, optimizations

## Questions?

Open an issue or reach out via GitHub discussions.

## Code of Conduct

Be respectful, constructive, and collaborative.
