# reasoning/dreamer.py
import time
from memory.neo4j_store import Neo4jMemoryStore
from config import OLLAMA_BASE_URL, GENERATION_MODEL
import requests
import json

def consolidate_memories(user_id: str):
    """
    Sleep Mode: Scans the graph for dense clusters and compresses them.
    Simulates human memory consolidation during sleep.
    """
    print(f"[Dreamer] Entering REM sleep for user {user_id}...")
    store = Neo4jMemoryStore()
    
    try:
        # 1. Find entities with too many edges (Clutter)
        # "Cognitive Load" check
        with store.driver.session() as session:
            result = session.run(
                """
                MATCH (n:Entity)-[r]-(m)
                WITH n, count(r) as degree
                WHERE degree > 3
                RETURN n.id as entity, degree
                ORDER BY degree DESC
                LIMIT 3
                """
            )
            candidates = [record["entity"] for record in result]
            
        print(f"[Dreamer] Found candidate concepts for consolidation: {candidates}")
        
        for entity_id in candidates:
            _process_cluster(store, user_id, entity_id)
            
    finally:
        store.close()

def _process_cluster(store, user_id, entity_id):
    # Get all facts about this entity
    with store.driver.session() as session:
        result = session.run(
            """
            MATCH (n:Entity {id: $id})-[r]-(m)
            RETURN type(r) as rel, m.id as neighbor, r.source_text as text, elementId(r) as edge_id
            LIMIT 10
            """,
            id=entity_id
        )
        facts = [dict(record) for record in result]
        
    if len(facts) < 3:
        return

    # Prepare for LLM
    fact_texts = [f"- {f['neighbor']} ({f['rel']})" for f in facts]
    fact_blob = "\n".join(fact_texts)
    
    print(f"[Dreamer] Dreaming about '{entity_id}'...\n{fact_blob}")
    
    prompt = f"""
    You are a Memory Consolidation System.
    The user has the following disjointed memories about '{entity_id}':
    {fact_blob}
    
    Can these be summarized into 1 or 2 high-level insights?
    If yes, provide a strict JSON summary.
    If they are unrelated, return strictly {{"consolidated": false}}.
    
    Example Input:
    - User (LIKES) Pizza
    - User (LIKES) Burgers
    - User (LIKES) Fries
    
    Example Output:
    {{
        "consolidated": true,
        "new_facts": [
            {{"relation": "LIKES", "target": "Junk Food", "confidence": 0.9}}
        ],
        "explanation": "Summarized specific fast foods into category 'Junk Food'"
    }}
    
    Return ONLY VALID JSON.
    """
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": GENERATION_MODEL, # Uses the smart model for complex reasoning
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )
        response.raise_for_status()
        data = json.loads(response.json()['response'])
        
        if data.get("consolidated"):
            print(f"[Dreamer] Insight: {data['explanation']}")
            # Apply changes
            for new_fact in data['new_facts']:
                store.insert_edge({
                    "src": entity_id,
                    "dst": new_fact['target'],
                    "relation": new_fact['relation'],
                    "confidence": new_fact.get('confidence', 0.9),
                    "user_id": user_id,
                    "source_text": f"Dream consolidation: {data['explanation']}"
                })
            
            # Prune old edges (optional, or just mark archived)
            # For hackathon safety, we won't delete yet, just reinforce the new one.
            # But "Crazy" idea says strict pruning. 
            # Let's delete them to prove the point.
            _prune_old_edges(store, facts)
            
    except Exception as e:
        print(f"[Dreamer] Nightmare (Error): {e}")

def _prune_old_edges(store, facts):
    edge_ids = [f["edge_id"] for f in facts]
    with store.driver.session() as session:
        # Cypher to delete by ID mechanism varies, using match for safety 
        # Actually elementId usage is specific.
        # We'll just skip complex deletion for now to avoid breaking the graph during verification.
        # Just logging.
        print(f"[Dreamer] (Would prune {len(edge_ids)} raw edges to save space)")
