# fast_pipe.py

import time
import requests
from requests.exceptions import ConnectionError

from diagnostics.logger import log_event
from llm.generator import generate_response
from memory.neo4j_store import Neo4jMemoryStore
from memory.vector_store import VectorMemoryStore
from reasoning.extractor import extract_graph_delta
from reasoning.reranker import rerank_memories
from slow_pipe import slow_pipe
from config import OLLAMA_BASE_URL, GENERATION_MODEL

import concurrent.futures

# Thread pool for background tasks (slow pipe)
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def _is_question(text: str) -> bool:
    """Simple heuristic to check if text is a question."""
    return text.strip().endswith("?") or any(w in text.lower() for w in ["who", "what", "where", "when", "why", "how"])

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
    - Retrieving from Neo4j + Chroma
    """

    start_time = time.time()
    memories = []
    
    # -------------------------
    # Step 0: FAST extraction + contradiction check (OPTIMIZED)
    # -------------------------
    # We need to extract early to check for contradictions BEFORE generating response
    # Optimizations: Limit fact checks to 3, reuse connection, skip on empty extraction
    graph_delta = extract_graph_delta(user_input)
    
    if graph_delta and graph_delta.get("edges"):
        from reasoning.omniscience import detect_contradiction
        from config import TRIVIAL_RELATIONS
        
        first_edge = graph_delta["edges"][0]
        
        # Only check meaningful facts for contradictions
        if first_edge['relation'] not in TRIVIAL_RELATIONS:
            log_event("LOGIC_BOMB_CHECK_START", edge=first_edge)
            store_check = Neo4jMemoryStore()
            try:
                # OPTIMIZATION: Limit to 3 most recent facts (was 5) to reduce latency
                related_facts = store_check.driver.session().run(
                    """
                    MATCH (s:Entity {id: $src})-[r]-(o)
                    RETURN s.id as src, type(r) as relation, o.id as dst
                    ORDER BY r.last_updated DESC
                    LIMIT 3
                    """,
                    src=first_edge['src']
                )
                
                fact_count = 0
                for record in related_facts:
                    fact_count += 1
                    existing_fact = {
                        "src": record["src"],
                        "relation": record["relation"],
                        "dst": record["dst"]
                    }
                    
                    log_event("LOGIC_BOMB_COMPARING", new_fact=first_edge, existing_fact=existing_fact)
                    
                    # Skip if existing fact is trivial
                    if existing_fact['relation'] in TRIVIAL_RELATIONS:
                        log_event("LOGIC_BOMB_SKIP", reason="trivial_relation", fact=existing_fact)
                        continue
                    
                    is_contradiction = detect_contradiction(first_edge, existing_fact)
                    if is_contradiction:
                        log_event("LOGIC_BOMB", reason="contradiction_blocked_before_response")
                        # Return early with user-friendly message - NO storage happens
                        response = "That contradicts what you told me earlier. I'll keep the original fact."
                        
                        return {
                            "response": response,
                            "memories_used": [],
                            "newly_extracted_graph": None,
                            "latency_ms": int((time.time() - start_time) * 1000)
                        }
                
                log_event("LOGIC_BOMB_CHECK_COMPLETE", facts_checked=fact_count, contradiction_found=False)
            finally:
                store_check.close()
        else:
            log_event("LOGIC_BOMB_SKIP", reason="trivial_new_relation", relation=first_edge['relation'])
    else:
        # No edges extracted, set to None for slow_pipe
        graph_delta = None

    try:
        # -------------------------
        # Step 1: Recent turns (for conversational fluency)
        # -------------------------
        recent_turns = ram_context.get(session_id)[-5:]

        # -------------------------
        # Step 2: Fast Semantic Gate
        # -------------------------
        if _requires_memory(user_input):
            
            # A. Symbolic Retrieval (Neo4j)
            neo4j_store = Neo4jMemoryStore()
            symbolic_context = neo4j_store.retrieve_context(user_id=session_id)
            neo4j_store.close()
            # Note: symbolic_context is a list of dicts (edges)
            
            # B. Neural Retrieval (Vector)
            vector_store = VectorMemoryStore()
            # Fetch more candidates for reranking (n=10)
            vector_results = vector_store.search(user_input, n_results=10, user_id=session_id)
            
            neural_memories = []
            if vector_results.get("documents"):
                docs = vector_results["documents"][0]
                metas = vector_results["metadatas"][0]
                for i, doc in enumerate(docs):
                    meta = metas[i] if i < len(metas) else {}
                    neural_memories.append({
                        "content": doc,
                        "type": "vector",
                        **meta
                    })

            # C. Hybrid Fusion & Cohere Reranking
            # We pass ALL candidates to the reranker
            # The reranker will use the API to find the absolute best matches
            memories = rerank_memories(user_input, symbolic_context, neural_memories, top_k=5)

        # -------------------------
        # Step 3: Context Compression
        # -------------------------
        from reasoning.compressor import ContextCompressor
        compressor = ContextCompressor(max_chars=2000)
        # Convert the list of best memories into a single optimized string
        memory_context_str = compressor.compress(memories)
        
        # -------------------------
        # Step 4: Generate response
        # -------------------------
        response = generate_response(
            user_input=user_input,
            recent_turns=recent_turns,
            memories=[memory_context_str], # Pass as single item list to fit generator signature
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
    # Step 4: Fire slow pipe for persistence ONLY (extraction already done)
    # -------------------------
    _executor.submit(slow_pipe, user_input, session_id, ram_context, graph_delta=graph_delta)

    # Return structured dictionary matching Hackathon Spec
    formatted_memories = []
    for m in memories:
        # Check if it's a Neo4j memory (symbolic) or Vector memory (neural)
        if "src" in m: # Symbolic
            formatted_memories.append({
                "memory_id": f"edge_{m.get('src')}_{m.get('dst')}",
                "content": f"{m.get('src')} {m.get('relation')} {m.get('dst')}",
                "origin_turn": m.get("turn_id", 0),
                "last_used_turn": int(m.get("last_updated", 0))  # simplified timestamp as turn proxy
            })
        else: # Neural
            formatted_memories.append({
                "memory_id": f"vec_{hash(m.get('content', ''))}",
                "content": m.get("content", ""),
                "origin_turn": m.get("turn_id", 0), # Vector store might not have this yet, default 0
                "last_used_turn": int(time.time())   # Current access
            })

    return {
        "response": response,
        "memories_used": formatted_memories,
        "newly_extracted_graph": None,
        "latency_ms": int((time.time() - start_time) * 1000)
    }
