# tests/verify_spreading_activation.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.neo4j_store import Neo4jMemoryStore

def test_spreading_activation():
    print("Testing Spreading Activation (Hunch Engine)...")
    store = Neo4jMemoryStore()
    
    # 1. Setup Data: Link 'ProjectAlpha' -> 'Deadline' -> 'NextWeek'
    # The user only mentions 'ProjectAlpha'. We expect 'NextWeek' to be retrieved via spread.
    print("  Seed data: User -> ProjectAlpha -> Deadline -> NextWeek")
    
    with store.driver.session() as session:
        # Cleanup
        session.run("MATCH (n:Entity {id: 'ProjectAlpha'}) DETACH DELETE n")
        session.run("MATCH (n:Entity {id: 'Deadline'}) DETACH DELETE n")
        session.run("MATCH (n:Entity {id: 'NextWeek'}) DETACH DELETE n")
        
        # User -(WorkingOn)-> ProjectAlpha -(Has)-> Deadline -(Is)-> NextWeek
        store.upsert_node("ProjectAlpha", "Project")
        store.upsert_node("Deadline", "Concept")
        store.upsert_node("NextWeek", "Time")
        
        # Direct edge (Recent)
        store.insert_edge({
            "src": "User", "dst": "ProjectAlpha", 
            "relation": "WorkingOn", "confidence": 1.0, 
            "user_id": "tester_spread"
        })
        
        # Indirect edges (Static Knowledge)
        store.insert_edge({
            "src": "ProjectAlpha", "dst": "Deadline", 
            "relation": "HasConstraint", "confidence": 0.9, 
            "user_id": "tester_spread"
        })
        
        store.insert_edge({
            "src": "Deadline", "dst": "NextWeek", 
            "relation": "IsDue", "confidence": 0.8, 
            "user_id": "tester_spread"
        })

    # 2. Query
    print("  Retrieving context for 'tester_spread'...")
    results = store.retrieve_context_with_activation("tester_spread", limit=10)
    
    # 3. Analyze
    found_indirect = False
    print(f"  Found {len(results)} potential memories:")
    for res in results:
        src, rel, dst = res['src'], res['relation'], res['dst']
        score = res.get('score', 0)
        depth = res.get('depth', -1)
        print(f"   [{depth}] {src} -[{rel}]-> {dst} (Score: {score:.2f})")
        
        if dst == "Deadline" or src == "Deadline":
            found_indirect = True
            
    if found_indirect:
        print("[+] Success! Found indirectly related node (Deadline) via spreading activation.")
    else:
        print("[-] Failed. Did not find indirect nodes.")
        
    store.close()

if __name__ == "__main__":
    test_spreading_activation()
