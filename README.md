# Memento

**Persistent semantic memory for AI agents.** Local, fast, and privacy-focused.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **🚀 Blazing Fast:** 0.03ms search via hybrid RAM/SQLite caching.
- **💾 Persistent:** Memories and cache survive restarts.
- **⚡ Hardware Accelerated:** Auto-uses AVX2/ONNX Runtime if available.
- **🧠 Semantic:** "Buy food" matches "Get groceries".
- **🖥️ CLI:** Rich terminal interface for human interaction.
- **☁️ Local First:** No API keys, no cloud dependencies.

## Quick Start

```bash
# Install
git clone https://github.com/rollersrights/memento.git
cd memento
pip install -r requirements.txt

# Store a memory
./memento remember "The server IP is 192.168.1.155" --tags "infra"

# Recall it
./memento recall "where is the server?"
```

## The CLI

Memento detects if you're a human or a script.

**Human Mode (Rich Tables):**
```text
ID        Score   Text
──────────────────────────────────────────
a1b2c3d4  0.89    The server IP is...
```

**Script Mode (JSON):**
```bash
./memento recall "server" | jq .[0].text
# "The server IP is 192.168.1.155"
```

## Architecture

```
┌──────────┐    ┌─────────────┐    ┌──────────────┐
│  Query   │───▶│  RAM Cache  │───▶│  Disk Cache  │
└──────────┘    │  (0.03ms)   │    │   (SQLite)   │
                └──────┬──────┘    └──────┬───────┘
                       │ (miss)           │ (miss)
                ┌──────▼──────┐           │
                │ ONNX/PyTorch│◀──────────┘
                │  Inference  │
                └─────────────┘
```

## Development

Run the test suite:
```bash
./run_tests.sh
```

## License

MIT
