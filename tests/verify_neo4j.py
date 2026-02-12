# tests/verify_neo4j.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.neo4j_store import Neo4jMemoryStore
import time

def test_neo4j_connection():
    print("Testing Neo4j Connection...")
    try:
        store = Neo4jMemoryStore()
        print("[+] Connection Successful!")
        
        # Test Wipe
        print("Testing Wipe...")
        store.wipe_database()
        
        # Test Insert
        print("Testing Insert...")
        store.upsert_node("Alice", "Person")
        store.upsert_node("Bob", "Person")
        store.insert_edge({
            "src": "Alice",
            "dst": "Bob",
            "relation": "KNOWS",
            "user_id": "test_user",
            "confidence": 0.9,
            "turn_id": 1,
            "source_text": "Alice knows Bob"
        })
        
        # Test Retrieval
        print("Testing Retrieval...")
        context = store.retrieve_context("test_user")
        if len(context) == 1 and context[0]["src"] == "Alice":
            print("[+] CRUD Operations Passed!")
        else:
            print(f"[-] CRUD Failed. Context: {context}")
            
        store.close()
        return True
    except Exception as e:
        print(f"[-] Neo4j Error: {e}")
        return False

if __name__ == "__main__":
    test_neo4j_connection()
