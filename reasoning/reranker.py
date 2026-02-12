from typing import Dict, List, Optional
import numpy as np
try:
    import cohere
except ImportError:
    cohere = None
from config import RERANKER_MODEL, COHERE_API_KEY

class Reranker:
    def __init__(self):
        self.cohere_client = None
        self.local_model = None
        
        if COHERE_API_KEY:
            try:
                self.cohere_client = cohere.Client(COHERE_API_KEY)
            except Exception as e:
                print(f"[Reranker] Failed to init Cohere: {e}")
        
        # Lazy load local model only if needed (or if we want a fallback)
        # For now, if we have Cohere, we skip loading the heavy local model to save RAM/Time
        if not self.cohere_client:
            print("[Reranker] Using Local Cross-Encoder (Slow)...")
            from sentence_transformers import CrossEncoder
            self.local_model = CrossEncoder(RERANKER_MODEL)

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        Rerank a list of memory candidates (Graph + Vector) using Cohere or Local Model.
        """
        if not candidates:
            return []

        # 1. Prepare documents for reranking
        # We need to map back to the original dictionary after reranking
        doc_texts = []
        for c in candidates:
            # Handle both graph edges and vector text
            if "relation" in c:
                # Symbolic: "Alice knows Bob"
                text = f"{c.get('src', 'User')} {c.get('relation', '')} {c.get('dst', '')}"
            else:
                # Vector: "I like coffee"
                text = c.get("content", "") or c.get("text", "")
            doc_texts.append(text)

        # 2. Rerank using Cohere (Fast & Better)
        if self.cohere_client:
            try:
                response = self.cohere_client.rerank(
                    model="rerank-english-v3.0",
                    query=query,
                    documents=doc_texts,
                    top_n=top_k,
                )
                
                ranked_results = []
                for result in response.results:
                    # result.index is the index in the original list
                    original_memory = candidates[result.index]
                    original_memory["score"] = result.relevance_score
                    ranked_results.append(original_memory)
                return ranked_results

            except Exception as e:
                print(f"[Reranker] Cohere API failed: {e}. Falling back to local.")
                # Fallthrough to local

        # 3. Fallback: Local Cross-Encoder (Slow)
        if self.local_model is None:
             from sentence_transformers import CrossEncoder
             self.local_model = CrossEncoder(RERANKER_MODEL)

        pairs = [[query, doc] for doc in doc_texts]
        scores = self.local_model.predict(pairs)
        
        # Attach scores and sort
        scored_candidates = []
        for i, score in enumerate(scores):
            cand = candidates[i]
            cand["score"] = float(score)
            scored_candidates.append(cand)

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]

# Global instance
_reranker_instance = None

def rerank_memories(
    query: str,
    symbolic_memories: List[Dict],
    neural_memories: List[Dict],
    top_k: int = 3
) -> List[Dict]:
    """
    Unified entry point for reranking.
    """
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()

    # Combine candidates (Hybrid Fusion Strategy: Simple Concatenation for now)
    # The Reranker itself acts as the fusion mechanism by scoring both types on the same scale.
    all_candidates = symbolic_memories + neural_memories
    
    return _reranker_instance.rerank(query, all_candidates, top_k=top_k)
