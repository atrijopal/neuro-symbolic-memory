# slow_pipe.py

import uuid
from diagnostics.logger import log_event
from config import MIN_CONFIDENCE_TO_STORE
from reasoning.confidence import compute_confidence

from memory.sqlite_store import SQLiteMemoryStore
from memory.vector_store import VectorMemoryStore


def slow_pipe(
    user_input: str,
    session_id: str,
    ram_context,
    graph_delta: dict = None,
):
    """
    SLOW PIPE (WRITE PATH)
    - Extracts graph deltas using Phi
    - Writes nodes + edges to SQLite
    - NEVER raises
    """

    try:
        # -------------------------
        # Step 1: Extraction (moved from fast pipe)
        # -------------------------
        # If graph_delta is not provided, extract it now (background)
        from reasoning.extractor import extract_graph_delta
        
        if graph_delta is None:
            graph_delta = extract_graph_delta(user_input)

        # -------------------------
        # Step 2: Check for graph delta
        # -------------------------
        if not graph_delta:
            log_event("SLOW_PIPE_ABORT", reason="no_graph_delta_extracted")
            return

        # -------------------------
        # Step 3: Confidence scoring (edge-level)
        # -------------------------
        confidence = compute_confidence(graph_delta)

        if confidence < MIN_CONFIDENCE_TO_STORE:
            log_event("SLOW_PIPE_ABORT", reason="low_confidence", score=confidence)
            return

        # -------------------------
        # Step 4: Persist graph
        # -------------------------
        store = SQLiteMemoryStore()

        # ---- Nodes ----
        for node in graph_delta.get("nodes", []):
            store.upsert_node(
                node_id=node["id"],
                node_type=node.get("type", "unknown"),
            )

        # ---- Edges ----
        turn_id = len(ram_context.get(session_id) or [])
        # Unique edge_id per turn to avoid primary key collision across turns
        for idx, edge in enumerate(graph_delta.get("edges", [])):
            store.insert_edge({
                # edge_id is now handled by insert_edge with hashing
                "edge_id": None, 
                "src": edge["src"],
                "dst": edge["dst"],
                "relation": edge["relation"],
                "confidence": confidence,
                "turn_id": turn_id,
                "user_id": session_id,
                "source_text": user_input,
            })

        # ---- Vector Store (Neural) ----
        # Store the raw text chunk for semantic retrieval
        vector_store = VectorMemoryStore()
        vector_store.add_memory(
            text=user_input,
            metadata={
                "user_id": session_id,
                "turn_id": turn_id,
                "confidence": confidence
            }
        )

        log_event(
            "SLOW_PIPE_OK",
            nodes=len(graph_delta.get("nodes", [])),
            edges=len(graph_delta.get("edges", [])),
            confidence=confidence,
        )

    except Exception as e:
        # Absolute safety: slow pipe must never crash fast pipe
        import traceback
        traceback.print_exc()
        log_event("SLOW_PIPE_ERROR", error=str(e))
        return
