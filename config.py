# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR_PATH = os.getenv("DATA_DIR", "data")

# Handle relative paths in env vars
if not os.path.isabs(DATA_DIR_PATH):
    DATA_DIR = BASE_DIR / DATA_DIR_PATH
else:
    DATA_DIR = Path(DATA_DIR_PATH)

SQLITE_DB_NAME = os.getenv("SQLITE_DB_PATH", "memory.db")
if os.path.basename(SQLITE_DB_NAME) == SQLITE_DB_NAME:
   SQLITE_DB_PATH = DATA_DIR / SQLITE_DB_NAME
else:
   SQLITE_DB_PATH = Path(SQLITE_DB_NAME)

CHROMA_DIR_NAME = os.getenv("CHROMA_DIR", "chroma")
if os.path.basename(CHROMA_DIR_NAME) == CHROMA_DIR_NAME:
    CHROMA_DIR = DATA_DIR / CHROMA_DIR_NAME
else:
    CHROMA_DIR = Path(CHROMA_DIR_NAME)


# -------------------------
# Neo4j Configuration
# -------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


# -------------------------
# Runtime parameters
# -------------------------
RAM_CONTEXT_SIZE = int(os.getenv("RAM_CONTEXT_SIZE", 8))
TOP_K_MEMORIES = int(os.getenv("TOP_K_MEMORIES", 3))
ASYNC_WORKERS = int(os.getenv("ASYNC_WORKERS", 1))

# -------------------------
# Confidence thresholds
# -------------------------
MIN_CONFIDENCE_TO_STORE = float(os.getenv("MIN_CONFIDENCE_TO_STORE", 0.65))
MIN_COREF_CONFIDENCE = float(os.getenv("MIN_COREF_CONFIDENCE", 0.8))

# -------------------------
# Model configuration
# -------------------------
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "llama3:8b")
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "phi3:mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# -------------------------
# LLM API (if using Ollama / local server)
# -------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# -------------------------
# External APIs
# -------------------------
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
