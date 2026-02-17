.PHONY: help install test lint format clean bench

help:
	@echo "Memento Development Commands"
	@echo ""
	@echo "  make install   Install dependencies"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make test      Run test suite"
	@echo "  make lint      Run linter (flake8)"
	@echo "  make format    Format code (black)"
	@echo "  make clean     Clean build artifacts"
	@echo "  make bench     Run benchmarks"
	@echo "  make ci        Run all CI checks"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev,fast]"

test:
	./run_tests.sh

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

format:
	black .

format-check:
	black . --check

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

bench:
	python3 benchmark.py
	python3 batch_benchmark.py

ci: lint test
	@echo "All CI checks passed!"

# Development helpers
quick-test:
	python3 -m pytest tests/test_core.py -v

profile:
	python3 -c "
	import cProfile
	import pstats
	from scripts.store import MemoryStore
	m = MemoryStore()
	cProfile.run('m.recall(\"test\")', '/tmp/profile.stats')
	p = pstats.Stats('/tmp/profile.stats')
	p.sort_stats('cumulative').print_stats(20)
	"
