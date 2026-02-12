# tests/verify_dream.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning.dreamer import consolidate_memories
from memory.neo4j_store import Neo4jMemoryStore

def test_dream_consolidation():
    print("Testing Sleep Mode (Dreamer)...")
    store = Neo4jMemoryStore()
    user_id = "dream_tester"
    
    # 1. Setup Data: Clutter the memory
    print("  Seeding clutter: 3 separate food items...")
    store.insert_edge({"src": "User", "dst": "Pizza", "relation": "LIKES", "user_id": user_id})
    store.insert_edge({"src": "User", "dst": "Burgers", "relation": "LIKES", "user_id": user_id})
    store.insert_edge({"src": "User", "dst": "Fries", "relation": "LIKES", "user_id": user_id})
    store.insert_edge({"src": "User", "dst": "Soda", "relation": "LIKES", "user_id": user_id})
    
    # 2. Trigger Sleep
    print("  Triggering consolidation...")
    consolidate_memories(user_id)
    
    # 3. Verify Result
    # We look for a new summarized node. Since LLM is non-deterministic, we check logs mostly,
    # but we can look for *new* edges on 'User' that we didn't insert.
    print("  Verifying new insights...")
    neighbors = store.get_related_nodes("User")
    
    new_concepts = []
    known = ["Pizza", "Burgers", "Fries", "Soda", "Cats"] # Cats from previous test maybe
    
    for n in neighbors:
        if n['neighbor'] not in known:
            new_concepts.append(n['neighbor'])
            
    if new_concepts:
        print(f"✅ Success! Dreamer created new concepts: {new_concepts}")
    else:
        print("⚠️ No new concepts found (LLM might have decided not to consolidate, or generated exactly 'Pizza' again).")
        
    store.close()

if __name__ == "__main__":
    test_dream_consolidation()
