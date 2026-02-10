# fast_pipe.py

import time
import requests
from concurrent.futures import ThreadPoolExecutor

from diagnostics.logger import log_event
from llm.generator import generate_response, _is_question
from memory.sqlite_store import SQLiteMemoryStore
from memory.vector_store import VectorMemoryStore
from reasoning.extractor import extract_graph_delta
from reasoning.reranker import rerank_memories
from slow_pipe import slow_pipe
from config import ASYNC_WORKERS, OLLAMA_BASE_URL, EXTRACTION_MODEL, TOP_K_MEMORIES


_executor = ThreadPoolExecutor(max_workers=ASYNC_WORKERS)

def _requires_memory(user_input: str) -> bool:
    """
    Fast semantic gate (Heuristic based).
    Returns True if answering requires stored memory.
    """
    # 1. Is it a question?
    if _is_question(user_input):
        return True
    
    # 2. Heuristics for implicit retrieval needs
    keywords = {"remember", "know", "recall", "told you", "earlier", "last time", "past"}
    if any(k in user_input.lower() for k in keywords):
        return True
        
    return False


def fast_pipe(user_input: str, session_id: str, ram_context):
    """
    FAST PIPE (READ PATH) - OPTIMIZED
    - No synchronous extraction (moved to slow pipe)
    - Fast heuristic memory gating
    - Deterministic and safe
    """

    start_time = time.time()
    memories = []
    
    # NOTE: We no longer extract graph delta here. 
    # It is extracted in the slow pipe to unblock the user response.

    try:
        # -------------------------
        # Step 1: Recent turns (for conversational fluency)
        # -------------------------
        recent_turns = ram_context.get(session_id)[-5:]

        # -------------------------
        # Step 2: Fast Semantic Gate
        # -------------------------
        if _requires_memory(user_input):
            # 2a. Symbolic Search (Graph)
            symbolic_memories = []
            try:
                sql_store = SQLiteMemoryStore()
                symbolic_memories = sql_store.retrieve_edges_for_user(session_id)
            except Exception as e:
                log_event("FAST_PIPE_WARN", reason="symbolic_search_failed", error=str(e))

            # 2b. Neural Search (Vector) - Filtered by session
            neural_memories = []
            try:
                vec_store = VectorMemoryStore()
                vec_results = vec_store.search(user_input, n_results=5, user_id=session_id)
                docs = (vec_results.get("documents") or [[]])[0]
                metadatas = (vec_results.get("metadatas") or [[]])[0]
                for i, doc in enumerate(docs):
                    # Only include if metadata matches session (double-check)
                    meta = metadatas[i] if i < len(metadatas) else {}
                    if not session_id or meta.get("user_id") == session_id:
                        neural_memories.append({
                            "content": doc,
                            "type": "vector",
                            "metadata": meta,
                        })
            except Exception as e:
                log_event("FAST_PIPE_WARN", reason="neural_search_failed", error=str(e))

            # 2c. Hybrid Reranking
            past_memories = rerank_memories(
                query=user_input,
                symbolic_memories=symbolic_memories,
                neural_memories=neural_memories,
                top_k=TOP_K_MEMORIES,
            )
            memories.extend(past_memories)

        # -------------------------
        # Step 3: Generate response
        # -------------------------
        response = generate_response(
            user_input=user_input,
            recent_turns=recent_turns, # This is passed but ignored in current generator (bug to fix later)
            memories=memories,
            session_id=session_id,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        log_event("FAST_PIPE_ERROR", error=str(e))
        response = "I apologize, but I'm having trouble retrieving my memories right now. Please try again in a moment."

    log_event(
        "FAST_PIPE_OK",
        latency_ms=int((time.time() - start_time) * 1000),
        memories_used=len(memories),
    )

    # -------------------------
    # Step 4: Fire slow pipe for persistence (Extraction happens there now)
    # -------------------------
    _executor.submit(slow_pipe, user_input, session_id, ram_context, graph_delta=None)

    # Return a structured dictionary for better testability and evaluation
    return {
        "response": response,
        "memories_used": memories,
        "newly_extracted_graph": None, # No longer available immediately
    }
