# Neuro-Symbolic Memory Agent

A hybrid AI memory system combining **Symbolic Graphs (SQLite)** for structured reasoning and **Neural Vectors (ChromaDB)** for semantic retrieval.

## Features
- **Fast Read Path**: Local heuristic memory gate + background extraction.
- **Dual Memory**: 
  - *Symbolic*: Stores entities and relations (e.g., `User --likes--> Pizza`).
  - *Neural*: Stores raw text chunks for semantic search.
- **Deduplication**: Content-based hashing prevents duplicate facts.
- **Robustness**: Graceful error handling and automatic retries.

## Setup

1. **Install Dependencies**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and update values if needed (e.g., Ollama URL).
   ```bash
   cp .env.example .env
   ```
   *Note: Requires [Ollama](https://ollama.com/) running with `llama3:8b` (generation) and `phi3:mini` (extraction).*

3. **Run**:
   ```bash
   python main.py
   ```
   Or run the Web UI:
   ```bash
   python web_ui.py
   ```

## Architecture
- **Fast Pipe**: Handles user interaction. retrieving memory, and generating responses.
- **Slow Pipe**: Runs in background to extract facts from user input and update the graph.
- **Storage**: SQLite (Graph), ChromaDB (Vectors).

## Testing
Run verification scripts:
```bash
python tests/verify_performance.py
python tests/verify_deduplication.py
```