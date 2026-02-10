# memory/chroma_store.py

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class ChromaMemoryStore:
    def __init__(self):
        self.client = chromadb.Client(
            Settings(
                persist_directory="data/chroma",
                anonymized_telemetry=False,
            )
        )

        self.collection = self.client.get_or_create_collection(
            name="memories"
        )

        # Correct, real model
        self.embedder = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

    def add(self, text: str, metadata: dict):
        embedding = self.embedder.encode(text).tolist()

        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[metadata.get("memory_id")],
        )

        self.client.persist()

    def query(self, query_text: str, top_k: int = 10):
        embedding = self.embedder.encode(query_text).tolist()

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )

        memories = []
        for i in range(len(results["documents"][0])):
            memories.append({
                "text": results["documents"][0][i],
                **results["metadatas"][0][i],
            })

        return memories
