#!/bin/bash
# Memento Test Runner

# Ensure we're in the right venv
source ~/.venv/bin/activate

# Path setup
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo "==========================================="
echo "🧪 MEMENTO TEST SUITE"
echo "==========================================="

echo -e "\n🔹 Running Core Functional Tests..."
python3 tests/test_core.py -v
CORE_EXIT=$?

echo -e "\n🔹 Running Cache Persistence Tests..."
python3 tests/test_cache.py -v
CACHE_EXIT=$?

echo "==========================================="
if [ $CORE_EXIT -eq 0 ] && [ $CACHE_EXIT -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
