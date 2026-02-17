# Cutting-Edge AI Memory Technologies Research Report
## February 2026 | For Memento Local-First Memory System

---

## Executive Summary

This report surveys the state-of-the-art in AI memory technologies as of February 2026, with specific recommendations for Memento—a local-first, SQLite-based memory system. The landscape has evolved dramatically, with context windows growing 30x annually, on-device embedding models achieving near-state-of-the-art performance, and hierarchical memory architectures becoming mainstream for agentic systems.

**Key Findings for Memento:**
- **sqlite-vec** is the ideal vector search solution for local-first deployment
- **EmbeddingGemma-300M** and **BGE-M3** offer excellent on-device embedding capabilities
- **Hierarchical memory architectures** (MemGPT-style) are essential for long-term agent memory
- **Matryoshka Representation Learning** enables flexible storage/quality trade-offs
- **Quantization techniques** (INT8, FP8, NVFP4) can reduce memory footprint by 50-75%

---

## 1. Vector Databases (2025-2026)

### 1.1 Market Overview

The vector database market has grown from $1.73 billion in 2024 to a projected $10.6 billion by 2032. Open-source adoption dominates, with Milvus leading at 35,000+ GitHub stars, followed by Qdrant (9,000+), Weaviate (8,000+), and ChromaDB (6,000+).

### 1.2 Major Players

| Database | Type | Best For | Key Strength | GitHub |
|----------|------|----------|--------------|--------|
| **Pinecone** | Managed | 10M-100M+ vectors | Easiest serverless, zero ops | N/A (proprietary) |
| **Milvus/Zilliz** | Open-source/Managed | Billions, enterprise | Most popular OSS, GPU acceleration | milvus-io/milvus |
| **Weaviate** | OSS + Managed | RAG <50M, hybrid search | Best hybrid search capabilities | weaviate/weaviate |
| **Qdrant** | OSS + Managed | <50M, filtering | Best free tier (1GB forever) | qdrant/qdrant |
| **pgvector** | PostgreSQL ext | Existing PG users | Unified data model, ACID | pgvector/pgvector |
| **ChromaDB** | OSS (embedded) | Prototypes <10M | Best developer experience | chroma-core/chroma |

### 1.3 Critical Innovation: sqlite-vec (For Memento)

**What is it?**
sqlite-vec is a zero-dependency C extension for SQLite that brings vector search capabilities to embedded databases. It's the successor to sqlite-vss, written in pure C with no external dependencies.

**Key Features:**
- Store and query float, int8, and binary vectors
- Runs anywhere SQLite runs (Linux/MacOS/Windows, WASM, Raspberry Pi)
- Supports metadata, auxiliary, and partition key columns
- Chunked storage—reads vectors in chunks, not entire dataset into memory
- Python, Node.js, Ruby, Go, Rust bindings available

**Performance Characteristics:**
- "Fast enough" for most local applications
- Memory-efficient chunked reading vs. DuckDB's full-load approach
- Suitable for 10K-10M vector ranges on consumer hardware

**Benefits:**
- ✅ Zero external dependencies
- ✅ Single-file database (SQLite)
- ✅ ACID compliance
- ✅ Cross-platform compatibility
- ✅ WASM support for browser/edge deployment

**Costs:**
- ❌ Not for billion-scale (use Milvus/Pinecone)
- ❌ No distributed querying
- ❌ Simpler indexing than HNSW (though HNSW support is planned)

**Suitability for Memento:** ⭐⭐⭐⭐⭐ EXCELLENT
- Perfect alignment with SQLite-based architecture
- Local-first by design
- Minimal dependencies

**Integration Difficulty:** LOW
```python
# pip install sqlite-vec
import sqlite_vec
# Load extension and create virtual tables
# See: https://alexgarcia.xyz/sqlite-vec/
```

**GitHub:** https://github.com/asg017/sqlite-vec

### 1.4 Recommendation for Memento

**Primary: sqlite-vec**
- Direct SQLite integration
- No separate infrastructure
- Perfect for local-first architecture

**Alternative for hybrid setups: pgvector**
- If PostgreSQL is already in stack
- More mature ecosystem
- Can handle 50M+ vectors with pgvectorscale

---

## 2. Embedding Models (State-of-the-Art 2026)

### 2.1 Key Trends

1. **Multilingual dominance**: 100+ language support is now standard
2. **Matryoshka Representation Learning (MRL)**: Truncatable embeddings (768→512→256→128 dims)
3. **Mixture-of-Experts (MoE)**: Dynamic parameter routing for efficiency
4. **On-device optimization**: Sub-500M parameter models with competitive performance
5. **Multimodal expansion**: Text+image+video embeddings emerging

### 2.2 Top Models for Local Deployment

| Model | Size | Context | Languages | MTEB Score | Best For |
|-------|------|---------|-----------|------------|----------|
| **EmbeddingGemma-300M** | 308M | 2K | 100+ | 64.5+ | On-device, mobile |
| **BGE-M3** | 568M | 8K | 100+ | 66.5+ | Multi-function (dense+sparse+multi-vector) |
| **Qwen3-Embedding-0.6B** | 600M | 32K | 100+ | 67+ | Long documents, flexible dims |
| **Nomic Embed Text v2** | 475M (MoE) | 512 | 100+ | 65+ | Cost-efficient at scale |
| **gte-multilingual-base** | 305M | 8K | 70+ | 64+ | Fast inference, encoder-only |
| **Jina Embeddings v4** | 3B | 8K | 30+ | 68+ | Multimodal (text+image+video) |

### 2.3 Deep Dive: EmbeddingGemma-300M (Top Pick for Memento)

**What is it?**
Google DeepMind's lightweight multilingual embedding model based on Gemma 3. Uses bidirectional attention (encoder architecture) with mean pooling and MRL.

**Architecture:**
- Bidirectional attention (not causal/decoders)
- Mean pooling over token embeddings
- Two dense layers → 768-dimensional output
- MRL supports truncation: 768→512→256→128

**Performance:**
- Under 200MB RAM with quantization
- <22ms embedding generation on EdgeTPU
- State-of-the-art for sub-500M parameter models

**Prompt Engineering Required:**
```python
# Query prompt
"task: search result | query: {text}"

# Document prompt
"title: none | text: {text}"
```

**Benefits:**
- ✅ Optimized for on-device deployment
- ✅ 100+ language support
- ✅ Apache 2.0 license
- ✅ MRL enables storage/quality trade-offs
- ✅ Integrates with sentence-transformers, LangChain, LlamaIndex

**Costs:**
- ❌ 2K context limit (shorter than some competitors)
- ❌ Requires prompt formatting for optimal results
- ❌ No float16 support (use float32/bfloat16)

**GitHub:** https://huggingface.co/google/embeddinggemma-300m

### 2.4 Deep Dive: BGE-M3 (Best for RAG)

**What is it?**
BAAI's "M3" = Multi-functionality, Multi-linguality, Multi-granularity. Supports dense retrieval, sparse retrieval (lexical), and multi-vector (ColBERT-style) simultaneously.

**Unique Features:**
- Dense + Sparse + Multi-vector in one model
- 8K token context
- 100+ languages
- Learnable dimensionality

**Benefits:**
- ✅ Three retrieval methods in one model
- ✅ Excellent for hybrid search scenarios
- ✅ Strong cross-lingual performance

**Costs:**
- ❌ Higher computational demand than EmbeddingGemma
- ❌ Larger model size (568M vs 308M)

**GitHub:** https://huggingface.co/BAAI/bge-m3

### 2.5 Recommendation for Memento

**Primary: EmbeddingGemma-300M**
- Best on-device performance
- Smallest memory footprint
- Excellent multilingual support

**Secondary: BGE-M3**
- When hybrid search (dense + lexical) is needed
- For longer document contexts (8K vs 2K)

**Inference Framework:**
- **sentence-transformers** (Python)
- **Transformers.js** (JavaScript/Web)
- **ONNX Runtime** (cross-platform, optimal for local)

---

## 3. Memory Architectures for AI Agents

### 3.1 The Agent Memory Taxonomy (2026)

Based on the comprehensive survey "Memory in the Age of AI Agents" (Dec 2025, arXiv:2512.13564), agent memory is categorized by:

**Forms (Storage Medium):**
1. **Token-level**: Explicit, discrete (vector DB, knowledge graphs)
2. **Parametric**: Implicit in model weights (fine-tuning, LoRA)
3. **Latent**: Hidden states, compressed representations

**Functions (Purpose):**
1. **Factual Memory**: Knowledge storage (RAG-style)
2. **Experiential Memory**: Learned skills, patterns from interactions
3. **Working Memory**: Active context management

**Dynamics (Lifecycle):**
1. **Formation**: Extraction and encoding
2. **Evolution**: Consolidation, forgetting, updating
3. **Retrieval**: Access strategies, relevance scoring

### 3.2 MemGPT / Letta (Hierarchical Memory Pioneer)

**What is it?**
MemGPT introduced "virtual context management"—treating LLM context like OS virtual memory, with data movement between fast (context window) and slow (external storage) tiers.

**Memory Tiers:**
1. **Main Context**: Current conversation (limited window)
2. **Archival Memory**: Vector database for long-term storage
3. **Recall Memory**: Working memory for recent relevant context

**Key Innovation:**
- Uses LLM itself to manage memory (self-editing)
- Function calling for memory operations (search, store, retrieve)
- Interrupts for control flow between user and system

**Evolution to Letta (2025):**
- MemGPT evolved into Letta (letta.com)
- Now a full platform for stateful agents
- Supports multiple memory blocks (human, persona, custom)
- Built-in tool calling and subagents

**Benefits:**
- ✅ Enables unlimited context through intelligent paging
- ✅ Agents can self-improve by updating memory
- ✅ Production-ready framework

**Costs:**
- ❌ Requires capable LLM for memory management
- ❌ Complexity in tuning memory policies

**GitHub:** https://github.com/letta-ai/letta

### 3.3 Recent Advances (2025-2026)

| Paper | Innovation | Relevance to Memento |
|-------|------------|---------------------|
| **MemoryOS** (Jun 2025) | Hierarchical memory integration + dynamic updating | Architecture inspiration |
| **Hierarchical Memory** (Jul 2025) | High-efficiency long-term reasoning | Implementation pattern |
| **G-Memory** (Jun 2025) | Hierarchical memory for multi-agent | Multi-user scenarios |
| **Mem0** (Apr 2025) | Production-ready scalable memory | API design patterns |
| **MIRIX** (Jul 2025) | Multi-agent memory system | Shared memory pools |

### 3.4 Recommendation for Memento

**Implement a Three-Tier Architecture:**

```
┌─────────────────────────────────────┐
│  TIER 1: Working Memory (Context)   │  ← Current conversation
│  - Active messages                  │    (limited by LLM context)
│  - Retrieved relevant memories      │
├─────────────────────────────────────┤
│  TIER 2: Episodic Memory (sqlite-vec)│  ← Recent interactions
│  - Recent conversations (hours-days)│    (fast retrieval)
│  - User preferences                 │
├─────────────────────────────────────┤
│  TIER 3: Semantic Memory (SQLite)   │  ← Long-term knowledge
│  - User profile                     │    (structured data)
│  - Learned facts                    │
│  - Important events                 │
└─────────────────────────────────────┘
```

**Key Principles:**
1. **Automatic summarization**: Compress old working memory → episodic
2. **Importance scoring**: Only important memories persist to semantic
3. **Temporal decay**: Less relevant memories fade over time
4. **User control**: Explicit memory editing capabilities

---

## 4. Context Window Management

### 4.1 Current State (February 2026)

Context windows have grown ~30x annually since mid-2023. Leading models:

| Model | Context Length | 80% Accuracy Length | Notes |
|-------|---------------|---------------------|-------|
| **Magic LTM-2-Mini** | 100M tokens | ~50M | Most extreme, code-focused |
| **Gemini 2.5 Pro** | 1M tokens | ~300K | Best production long-context |
| **Qwen3-Coder-480B** | 256K (extendable to 1M) | ~150K | MoE architecture |
| **DeepSeek-R1** | 164K | ~100K | Reasoning-focused |
| **Llama 4 Scout** | 256K | ~120K | Open weights |

### 4.2 Context Management Techniques

**1. Retrieval-Augmented Generation (RAG)**
- External vector database for long-term memory
- Query → Retrieve → Augment prompt → Generate
- Standard approach for document Q&A

**2. Hierarchical Summarization**
- Compress older context into summaries
- Recursive summarization for very long contexts
- Trade-off: detail vs. coverage

**3. Selective Attention / KV Cache Compression**
- Keep only "important" tokens in cache
- Eviction policies based on attention patterns
- Enables longer effective context

**4. Sliding Window / Chunking**
- Process documents in overlapping chunks
- Aggregate results
- Common for very long documents

### 4.3 Recommendation for Memento

**Hybrid Approach:**

1. **For conversation history**: 
   - Keep recent N messages in full (working memory)
   - Summarize older exchanges into episodic memory
   
2. **For document understanding**:
   - Use RAG with sqlite-vec for document chunks
   - Retrieve relevant sections into context

3. **Memory injection**:
   - Always include critical user facts in system prompt
   - Use retrieval to find relevant past interactions

---

## 5. Hierarchical Memory Systems

### 5.1 Human-Inspired Architecture

Modern agent memory systems increasingly mirror human memory:

```
┌─────────────────────────────────────────┐
│  SENSORY MEMORY (Immediate)             │
│  - Current context window               │
│  - ~4K-128K tokens (LLM-dependent)      │
│  - Duration: seconds to minutes         │
├─────────────────────────────────────────┤
│  SHORT-TERM / WORKING MEMORY            │
│  - Active conversation                  │
│  - Retrieved relevant memories          │
│  - Duration: current session            │
├─────────────────────────────────────────┤
│  LONG-TERM MEMORY                       │
│  ├─ Episodic: Events, experiences       │
│  ├─ Semantic: Facts, knowledge          │
│  └─ Procedural: Skills, patterns        │
│  Duration: days to years                │
└─────────────────────────────────────────┘
```

### 5.2 Implementation Patterns

**1. Nemori (Aug 2025)**
- Self-organizing memory inspired by cognitive science
- Automatic clustering and connection of related memories

**2. HippoRAG (May 2024)**
- Neurobiologically-inspired long-term memory
- Personalization through continuous learning

**3. A-MEM (Feb 2025)**
- Agentic memory with self-improvement
- RL-based memory management

### 5.3 Recommendation for Memento

**Implement Cognitive Science Principles:**

1. **Spaced Repetition**: Review important memories at increasing intervals
2. **Elaborative Encoding**: Connect new memories to existing knowledge
3. **Retrieval Practice**: Active recall strengthens memory
4. **Forgetting Curve**: Less important memories fade naturally
5. **Consolidation**: Sleep/downtime processes for memory optimization

---

## 6. Sparse Attention Mechanisms

### 6.1 The Attention Bottleneck

Standard transformer attention is O(n²) in sequence length—prohibitively expensive for long contexts. Sparse attention reduces this to O(n log n) or O(n).

### 6.2 Key Techniques

| Technique | Approach | Complexity | Status |
|-----------|----------|------------|--------|
| **FlashAttention** | IO-aware exact attention | O(n²) but faster | Production standard |
| **Sliding Window** | Local attention only | O(n × window) | Widely used |
| **Sparse Transformers** | Fixed sparse patterns | O(n √n) | Research |
| **Linformer** | Low-rank attention | O(n) | Limited adoption |
| **RWKV** | RNN-like linear attention | O(n) | Emerging |
| **Mamba** | State space models | O(n) | Growing adoption |

### 6.3 FlashAttention 3 (2025)

- Hardware-optimized for H100 GPUs
- Near-memory computing for KV cache
- Up to 2x speedup over FlashAttention 2
- Native FP8 support

### 6.4 Recommendation for Memento

**For inference optimization:**
- Use **FlashAttention** for LLM inference if running locally with GPU
- **Sliding window attention** (e.g., Mistral-style) for very long sequences
- Consider **Mamba** or **RWKV** architectures for new model development

---

## 7. Memory Compression Techniques

### 7.1 KV Cache Optimization

The KV cache often exceeds model weights in memory usage for long contexts. Compression techniques:

| Technique | Compression | Accuracy Impact | Hardware |
|-----------|-------------|-----------------|----------|
| **FP16 → FP8** | 2x | <1% loss | NVIDIA Ada/Hopper |
| **FP8 → NVFP4** | 2x (4x total) | <1% loss | Blackwell GPUs |
| **INT8 Quantization** | 2x | 1-2% loss | Most GPUs |
| **INT4 Quantization** | 4x | 2-5% loss | Specialized |
| **KV Cache Eviction** | Variable | Task-dependent | All |

### 7.2 Advanced Compression (2025-2026)

**1. ChunkKV (Oct 2025)**
- Semantic-preserving KV cache compression
- Groups semantically similar tokens
- Up to 4x compression with minimal accuracy loss

**2. ZipCache (2025)**
- Salient token identification
- Keeps only "important" tokens based on attention patterns

**3. OjaKV (2025)**
- Online low-rank compression
- Adapts to context in real-time

### 7.3 Embedding Compression

**Matryoshka Representation Learning (MRL):**
- Train embeddings to be truncatable
- Store 768-dim, use 256-dim for faster retrieval
- 3x storage reduction, minimal accuracy loss

### 7.4 Recommendation for Memento

**For storage efficiency:**

1. **Quantize embeddings**: Store as INT8 or even binary (for some use cases)
2. **MRL truncation**: Use 256-dim instead of 768-dim where acceptable
3. **sqlite-vec INT8 support**: Store vectors as 8-bit integers
4. **Differential storage**: Only store changes/diffs for memory updates

---

## 8. On-Device vs Cloud Memory Trade-offs

### 8.1 Comparison Matrix

| Factor | On-Device | Cloud |
|--------|-----------|-------|
| **Latency** | <10ms (local) | 50-200ms (network) |
| **Privacy** | Excellent (data never leaves) | Requires trust |
| **Cost** | Hardware only | Per-token/usage pricing |
| **Scale** | Limited by device | Virtually unlimited |
| **Offline** | Works without internet | Requires connectivity |
| **Updates** | Manual/periodic | Continuous |
| **Power** | Battery-constrained | Unlimited |

### 8.2 On-Device Feasibility (2026)

**What runs well locally:**
- Embedding models up to 1B parameters (EmbeddingGemma, BGE-M3)
- Small LLMs for memory management (3B-8B parameters)
- Vector search on 100K-10M vectors (sqlite-vec)
- Full RAG pipeline

**What requires cloud:**
- Large reasoning models (70B+ parameters)
- Massive-scale vector search (100M+ vectors)
- Multi-modal large models

### 8.3 Hybrid Architectures

**Edge-Cloud Split:**
- **Edge**: Embedding generation, local retrieval, fast-path responses
- **Cloud**: Complex reasoning, large-scale memory search, model updates

**Recommendation for Memento:**

**Pure Local-First Approach:**
- All user data stays on device
- Use quantized models for efficiency
- sqlite-vec for vector storage
- Sync across devices optional (encrypted)

**Optional Cloud Enhancement:**
- Offload complex reasoning to cloud APIs when needed
- Cloud backup of encrypted memory
- No mandatory cloud dependencies

---

## 9. Concrete Recommendations for Memento

### 9.1 Technology Stack

| Component | Recommendation | Alternative |
|-----------|---------------|-------------|
| **Vector Database** | sqlite-vec | pgvector (if using PostgreSQL) |
| **Embedding Model** | EmbeddingGemma-300M | BGE-M3 (for hybrid search) |
| **Inference** | ONNX Runtime | sentence-transformers |
| **Memory Architecture** | MemGPT-style 3-tier | Custom hierarchical |
| **Compression** | MRL truncation + INT8 | FP8 (if GPU available) |
| **LLM (local)** | Llama 3.x 8B Q4 | Qwen3 7B |
| **LLM (cloud)** | GPT-4.1 mini | Claude 3.5 Haiku |

### 9.2 Implementation Roadmap

**Phase 1: Foundation (Months 1-2)**
1. Integrate sqlite-vec for vector storage
2. Implement EmbeddingGemma for embeddings
3. Basic RAG retrieval pipeline
4. Simple working memory (last N messages)

**Phase 2: Hierarchical Memory (Months 3-4)**
1. Implement episodic memory tier
2. Automatic conversation summarization
3. Importance scoring for memory retention
4. Memory search/retrieval UI

**Phase 3: Intelligence (Months 5-6)**
1. Self-improving memory management
2. User preference learning
3. Cross-device sync (encrypted)
4. Advanced retrieval (hybrid search)

### 9.3 Code Snippets

**sqlite-vec Integration:**
```python
import sqlite3
import sqlite_vec

# Load extension
db = sqlite3.connect("memento.db")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Create virtual table
db.execute("""
    CREATE VIRTUAL TABLE memories USING vec0(
        embedding FLOAT[768],
        memory_type TEXT,
        timestamp INTEGER,
        content TEXT
    )
""")

# Insert with metadata
db.execute("""
    INSERT INTO memories(rowid, embedding, memory_type, timestamp, content)
    VALUES (?, ?, ?, ?, ?)
"", (memory_id, embedding_bytes, "episodic", timestamp, content))

# Search
results = db.execute("""
    SELECT rowid, distance, content
    FROM memories
    WHERE embedding MATCH ?
    AND memory_type = 'episodic'
    ORDER BY distance
    LIMIT 10
"", (query_embedding,)).fetchall()
```

**Embedding Generation:**
```python
from sentence_transformers import SentenceTransformer

# Load model with MRL truncation
model = SentenceTransformer("google/embeddinggemma-300m", truncate_dim=256)

# Encode with appropriate prompt
embedding = model.encode(
    "Remember that I prefer dark mode",
    prompt_name="Clustering"  # or custom prompt
)
```

**Memory Hierarchy:**
```python
class MemoryManager:
    def __init__(self):
        self.working_memory = []  # Current conversation
        self.episodic_db = sqlite_vec_db()  # Recent events
        self.semantic_db = sqlite_db()  # Long-term facts
    
    def add_interaction(self, user_msg, assistant_msg):
        # Add to working memory
        self.working_memory.extend([user_msg, assistant_msg])
        
        # Check if working memory is full
        if self.working_memory_too_large():
            self._consolidate_to_episodic()
    
    def retrieve_relevant(self, query, k=5):
        # Search all tiers
        episodic = self.episodic_db.search(query, k=k//2)
        semantic = self.semantic_db.search(query, k=k//2)
        return self._merge_and_rank(episodic, semantic)
```

---

## 10. Key Research Papers & Repositories

### Must-Read Papers

1. **"Memory in the Age of AI Agents: A Survey"** (Dec 2025)
   - arXiv:2512.13564
   - Comprehensive taxonomy of agent memory
   - https://github.com/Shichun-Liu/Agent-Memory-Paper-List

2. **"MemGPT: Towards LLMs as Operating Systems"** (Oct 2023)
   - arXiv:2310.08560
   - Hierarchical memory architecture
   - https://github.com/letta-ai/letta

3. **"KV Cache Compression for Inference Efficiency in LLMs: A Review"** (Aug 2025)
   - arXiv:2508.06297
   - Comprehensive survey of compression techniques

### Key GitHub Repositories

| Repository | Description | URL |
|------------|-------------|-----|
| **sqlite-vec** | SQLite vector search extension | github.com/asg017/sqlite-vec |
| **sentence-transformers** | Embedding model framework | github.com/UKPLab/sentence-transformers |
| **letta** | Stateful agent platform (MemGPT successor) | github.com/letta-ai/letta |
| **transformers.js** | On-device ML for web | github.com/huggingface/transformers.js |
| **Mem0** | Production memory for AI agents | github.com/mem0ai/mem0 |

---

## 11. Summary & Final Recommendations

### For Memento specifically:

1. **Use sqlite-vec** as the vector database—it's purpose-built for local-first, SQLite-based applications

2. **Adopt EmbeddingGemma-300M** for on-device embeddings—optimal balance of quality, size, and speed

3. **Implement a 3-tier memory hierarchy** (working → episodic → semantic) following MemGPT's architecture

4. **Leverage Matryoshka Representation Learning** to offer users quality/storage trade-offs

5. **Quantize aggressively**—INT8 embeddings, FP8/FP4 KV cache if using GPU

6. **Keep it local-first**—all data stays on device, with optional encrypted sync

7. **Follow cognitive science principles**—spaced repetition, elaborative encoding, retrieval practice

### Competitive Advantages for Memento:

- **True local-first**: No cloud dependency required
- **SQLite-native**: Single-file, portable databases
- **Privacy-preserving**: User data never leaves device
- **Efficient**: Optimized for consumer hardware
- **Open**: Built on open-source technologies

---

*Report compiled: February 17, 2026*
*Sources: arXiv papers, GitHub repositories, vendor documentation, MTEB leaderboard*
