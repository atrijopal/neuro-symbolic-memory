# 🧠 Neuro-Symbolic Memory Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.15-018bff)](https://neo4j.com/)
[![Ollama](https://img.shields.io/badge/Ollama-llama3-black)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **A cutting-edge cognitive architecture merging Neural Networks (LLMs) with Symbolic AI (Knowledge Graphs) for long-term, consistent, and self-correcting memory.**

Built for **Neurohack Hackathon 2026** | [📚 Full Documentation](DOCUMENTATION.md) | [🎬 Demo Notebook](run_demo.ipynb)

---

## ✨ What Makes This Special?

Unlike traditional RAG systems that simply retrieve documents, this agent **thinks** like a human brain:

- 🔗 **Spreading Activation**: Connects concepts laterally (ask about "hiking" → recalls "Seattle rain")
- 💤 **Memory Consolidation**: Compresses memories during "sleep" (multiple pizza mentions → "likes Italian food")
- 💣 **Conflict Detection**: Catches contradictions before they corrupt memory
- ⚡ **Dual-Process Architecture**: Fast retrieval (System 1) + Deep reasoning (System 2)

## 🚀 Quick Start

### Prerequisites

Ensure you have installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [Neo4j Desktop](https://neo4j.com/download/) (or Docker)
- [Ollama](https://ollama.ai/download)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/neuro-symbolic-memory.git
cd neuro-symbolic-memory

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Neo4j credentials and API keys

# Pull required models
ollama pull llama3:8b
ollama pull phi3:mini
```

### Run the Application

**Option 1: Web Interface**
```bash
python web_ui.py
# Open http://localhost:8000
```

**Option 2: CLI**
```bash
python main.py
```

**Option 3: Interactive Demo**
```bash
jupyter notebook run_demo.ipynb
```

## 🏗️ Architecture

```
User Input
    ↓
Fast Pipe (System 1)              Slow Pipe (System 2)
├─ Heuristic Gate                 ├─ Graph Extraction
├─ Hybrid Retrieval               ├─ Conflict Detection  
├─ Cohere Reranking               ├─ Confidence Scoring
├─ Context Compression            └─ Neo4j + ChromaDB Write
├─ LLM Generation (llama3:8b)
└─ Response (8-12s)               └─ Background (4-6s)
```

**Memory Stores:**
- **Neo4j**: Symbolic knowledge graph (facts & relationships)
- **ChromaDB**: Vector embeddings (semantic search)
- **RAMContext**: Short-term conversational memory

## 🎯 Key Features

### 1. Spreading Activation
Traditional systems only retrieve exact matches. We simulate how the brain recalls related concepts:

```python
Query: "Do I need rain gear for my hobby?"
├─ Activates: hiking → Seattle → rain
└─ Response: "Living in Seattle, you should always carry rain gear for your hikes!"
```

### 2. Dream Consolidation
Reduces graph complexity by identifying patterns:

```python
Before Dreaming:
- User ate Pizza (Monday)
- User ate Pasta (Tuesday)  
- User ate Lasagna (Wednesday)

After Dreaming:
- User LIKES Italian_Cuisine (confidence: 0.9)
```

### 3. Logic Bomb Detector
Prevents contradictory memories:

```python
New: "I hate pizza"
Existing: "I love pizza"
→ Conflict detected! Flag for review or update with declining confidence.
```

## 📊 Performance

| Metric | Production Target (GPU) | Local Dev (CPU) |
|--------|-------------------------|-----------------|
| **Full Pipeline** | **< 3.0s** (Real-Time) | ~15-20s |
| **Retrieval (System 1)** | **~250ms** | ~2.4s |
| **Generation (Llama-3)** | **~50ms/tok** | ~5-10 tok/s |
| **Recall Accuracy** | **98%** | 98% (Logic Verified) |

> **Note:** The architecture is designed for speed. Local latency is dominated by CPU inference of 8B parameter models. On a T4/A100, this system runs in real-time.

## 📁 Project Structure

```
neuro-symbolic-memory/
├── fast_pipe.py          # ⚡ System 1: Fast Retrieval & Generation
├── slow_pipe.py          # 🧠 System 2: Deep Reasoning & Extraction
├── main.py               # 🖥️ CLI Entry Point
├── web_ui.py             # 🌐 Web Dashboard (FastAPI)
├── config.py             # ⚙️ Global Configuration
├── llm/                  # 🤖 Model Interfaces
│   ├── generator.py      # Llama-3 Interface
│   └── verifier.py       # Hallucination Checks
├── memory/               # 💾 Long-Term Memory Layer
│   ├── neo4j_store.py    # Graph Database (Symbolic)
│   ├── vector_store.py   # ChromaDB (Neural Embeddings)
│   └── ram_context.py    # Short-Term Working Memory
├── reasoning/            # 🧩 Cognitive Modules
│   ├── extractor.py      # Knowledge Graph Construction
│   ├── dreamer.py        # Sleep Consolidation (Graph Compression)
│   ├── omniscience.py    # Logic Bomb & Conflict Detector
│   ├── reranker.py       # Hybrid Reranking (Cross-Encoder)
│   └── compressor.py     # Context Optimization
├── evaluation/           # 📊 Benchmarks & Metrics
├── tests/                # ✅ Unit & Integration Tests
├── static/               # 🎨 Frontend Assets
└── templates/            # HTML templates
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/test_cognitive.py -v

# Check infrastructure
python -c "from memory.neo4j_store import Neo4jMemoryStore; Neo4jMemoryStore()"

# Run demo
jupyter notebook run_demo.ipynb
```

## 📖 Documentation

For comprehensive documentation including:
- Complete file inventory (all 51 Python files)
- Real performance benchmarks
- API requirements (Cohere, HuggingFace)
- Step-by-step setup guide
- Feature demonstrations
- Troubleshooting

See **[DOCUMENTATION.md](DOCUMENTATION.md)**

## 🔑 API Keys

### Required
- **Cohere API Key**: For memory reranking ([Get key](https://dashboard.cohere.com/api-keys))
  - Free tier: 100 calls/month
  - Fallback: Uses HuggingFace cross-encoder if unavailable

### Optional
- **HuggingFace Token**: Only for private models ([Get token](https://huggingface.co/settings/tokens))
  - Public models auto-download without authentication

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) file

## 🏆 Acknowledgments

Built for **Neurohack Hackathon 2026**

**Team**: Atrijo Pal & Isam Ahammed (ELECTRO_AI)

**Technologies**: Neo4j, Ollama, ChromaDB, FastAPI, llama3, phi3

---

⭐ **Star this repo if you find it useful!**