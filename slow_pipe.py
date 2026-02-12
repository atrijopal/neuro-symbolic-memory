# slow_pipe.py

import uuid
from diagnostics.logger import log_event
from config import MIN_CONFIDENCE_TO_STORE
from reasoning.confidence import compute_confidence

from memory.neo4j_store import Neo4jMemoryStore
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
    - Writes nodes + edges to Neo4j
    - NEVER raises
    """

    try:
        # -------------------------
        # Step 1: Extraction (moved from fast pipe)
        # -------------------------
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
        # Step 3.5: Logic Bomb / Contradiction Check
        # -------------------------
        from reasoning.omniscience import detect_contradiction
        
        if graph_delta.get("edges"):
            first_edge = graph_delta["edges"][0]
            
            # Check against existing knowledge
            store_check = Neo4jMemoryStore()
            try:
                # Find facts about the same subject
                # Limit to 5 most recent to save time/tokens
                related_facts = store_check.driver.session().run(
                    """
                    MATCH (s:Entity {id: $src})-[r]-(o)
                    RETURN s.id as src, type(r) as relation, o.id as dst
                    ORDER BY r.last_updated DESC
                    LIMIT 5
                    """,
                    src=first_edge['src']
                )
                
                for record in related_facts:
                    existing_fact = {
                        "src": record["src"],
                        "relation": record["relation"],
                        "dst": record["dst"]
                    }
                    
                    is_contradiction = detect_contradiction(first_edge, existing_fact)
                    if is_contradiction:
                        print(f"💣 [Logic Bomb] Contradiction detected vs '{existing_fact}'! Rejecting: {first_edge}")
                        log_event("SLOW_PIPE_ABORT", reason="logic_bomb_contradiction", edge=first_edge, conflicting_with=existing_fact)
                        return
            finally:
                store_check.close()

        # -------------------------
        # Step 4: Persist graph (Neo4j)
        # -------------------------
        store = Neo4jMemoryStore()

        # ---- Nodes ----
        for node in graph_delta.get("nodes", []):
            store.upsert_node(
                node_id=node["id"],
                node_type=node.get("type", "unknown"),
            )

        # ---- Edges ----
        turn_id = len(ram_context.get(session_id) or [])
        
        for idx, edge in enumerate(graph_delta.get("edges", [])):
            # Use specific edge confidence if available, else fallback to global score
            edge_confidence = edge.get("confidence", confidence)
            
            store.insert_edge({
                "src": edge["src"],
                "dst": edge["dst"],
                "relation": edge["relation"],
                "confidence": edge_confidence,
                "turn_id": turn_id,
                "user_id": session_id,
                "source_text": user_input,
            })
            
        store.close()

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
