# tests/verify_conflict.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning.omniscience import detect_contradiction
from memory.neo4j_store import Neo4jMemoryStore
from slow_pipe import slow_pipe
import time

def test_conflict_detection():
    print("Testing Conflict Resolution (Omniscience)...")
    
    # 1. Unit Test
    fact_a = {"src": "User", "relation": "LIKES", "dst": "Pizza"}
    fact_b = {"src": "User", "relation": "LIKES", "dst": "Sushi"}
    fact_c = {"src": "User", "relation": "HATES", "dst": "Pizza"}
    
    print("  Checking: Likes Pizza vs Likes Sushi (Expect False)")
    conflict_1 = detect_contradiction(fact_a, fact_b)
    print(f"  Result: {conflict_1}")
    
    print("  Checking: Likes Pizza vs Hates Pizza (Expect True)")
    conflict_2 = detect_contradiction(fact_c, fact_a)
    print(f"  Result: {conflict_2}")
    
    if not conflict_1 and conflict_2:
        print("[+] Unit Test Passed")
    else:
        print("[-] Unit Test Failed")
        
    # 2. Integration Test (Simulated)
    # We can't easily mock the Slow Pipe thread here without complex setup, 
    # but we can verify the Neo4j query logic manually.
    store = Neo4jMemoryStore()
    store.upsert_node("User", "Person")
    store.insert_edge({"src": "User", "dst": "Cats", "relation": "LIKES", "confidence": 0.9, "user_id": "test_conflict"})
    
    others = store.get_related_nodes("User")
    # Verify we can find the edge
    found = False
    for o in others:
        if o['neighbor'] == "Cats" and o['relation'] == "LIKES":
            found = True
    
    if found:
        print("[+] Integration Query Logic Passed")
    else:
        print("[-] Integration Query Logic Failed")
        
    store.close()

if __name__ == "__main__":
    test_conflict_detection()
