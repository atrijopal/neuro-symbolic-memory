# reasoning/reranker.py

from typing import Dict, List
import numpy as np
from sentence_transformers import CrossEncoder
from config import RERANKER_MODEL

_model = None

def _get_model():
    global _model
    if _model is None and RERANKER_MODEL:
        _model = CrossEncoder(RERANKER_MODEL)
    return _model


def rerank_memories(
    query: str,
    symbolic_memories: List[Dict],
    neural_memories: List[Dict],
    top_k: int = 3
) -> List[Dict]:
    """
    Rerank memories using Cross-Encoder (Hybrid Search).
    """
    candidates = []

    # 1. Normalize Symbolic Memories (Graph)
    for mem in symbolic_memories:
        # Convert structured edge to natural language for reranking
        text = f"{mem.get('src', 'User')} {mem.get('relation', '')} {mem.get('dst', '')}"
        candidates.append({
            "text": text,
            "memory": mem,
            "score": mem.get("confidence", 0.0)  # Base score
        })

    # 2. Normalize Neural Memories (Vector)
    for mem in neural_memories:
        candidates.append({
            "text": mem.get("content", ""),
            "memory": mem,
            "score": 0.0
        })

    if not candidates:
        return []

    # 3. Apply Cross-Encoder Reranking
    model = _get_model()
    if model:
        try:
            pairs = [[query, c["text"]] for c in candidates]
            raw = model.predict(pairs)
            scores = np.asarray(raw).flatten()
            for i in range(min(len(scores), len(candidates))):
                candidates[i]["score"] = float(scores[i])
        except Exception:
            pass  # Keep existing scores (e.g. symbolic confidence)
    else:
        pass  # Fallback: sort by existing scores only

    # 4. Sort and Slice
    candidates.sort(key=lambda x: x["score"], reverse=True)

    return [c["memory"] for c in candidates[:top_k]]
