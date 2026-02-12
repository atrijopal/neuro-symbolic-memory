# memory/vector_store.py

import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from config import CHROMA_DIR, EMBEDDING_MODEL

# --- Singleton pattern for Chroma client ---
_client = None

def _get_client():
    """Get a singleton ChromaDB client."""
    global _client
    if _client is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def reset_client():
    """Drop the Chroma client so the next use creates a fresh one (e.g. after wipe)."""
    global _client
    _client = None
# ---

class VectorMemoryStore:
    """
    A wrapper around a ChromaDB collection for vector-based memory storage and retrieval.
    """
    def __init__(self, collection_name: str = "neuro_symbolic_memory"):
        self.client = _get_client()
        
        # Use the SentenceTransformer embedding function from chromadb utils
        # This will handle downloading and using the model specified in config.
        # Explicitly specify device='cpu' to avoid torch meta tensor errors
        st_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device='cpu'
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=st_ef
        )

    def _compute_doc_id(self, user_id: str, text: str) -> str:
        """Generate deterministic ID for vector memory."""
        import hashlib
        content = f"{user_id}:{text.strip()}"
        return hashlib.md5(content.encode()).hexdigest()

    def add_memory(self, text: str, metadata: dict):
        """Add a memory chunk (text) to the vector store."""
        
        user_id = metadata.get("user_id", "unknown")
        doc_id = self._compute_doc_id(user_id, text)
        
        # Use upsert to handle duplicates (ChromaDB supports upsert)
        self.collection.upsert(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def search(self, query_text: str, n_results: int = 5, user_id: str = None) -> dict:
        """
        Search for memory chunks similar to the query text.
        Optionally filter by user_id for session isolation.
        """
        try:
            where = None
            if user_id:
                where = {"user_id": user_id}
            
            return self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
            )
        except Exception:
            # Return empty results on failure to prevent crashes
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}