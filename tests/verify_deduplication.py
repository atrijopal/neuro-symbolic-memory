import sys
import os
import hashlib
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.sqlite_store import SQLiteMemoryStore
from memory.vector_store import VectorMemoryStore
from config import SQLITE_DB_PATH

def test_sqlite_deduplication():
    print("Testing SQLite Deduplication...")
    store = SQLiteMemoryStore()
    
    # Clear edges for testing
    conn = store.conn
    conn.execute("DELETE FROM edges WHERE user_id='test_user'")
    conn.commit()
    
    edge = {
        "edge_id": None, # Should be auto-generated
        "src": "User",
        "dst": "Coffee",
        "relation": "likes",
        "user_id": "test_user",
        "source_text": "I like coffee"
    }
    
    # Insert twice
    store.insert_edge(edge)
    store.insert_edge(edge)
    
    # Check count
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM edges WHERE user_id='test_user'")
    count = cur.fetchone()[0]
    
    if count == 1:
        print("✅ SQLite Deduplication Passed: 1 edge found after 2 inserts.")
    else:
        print(f"❌ SQLite Deduplication Failed: {count} edges found.")

def test_vector_deduplication():
    print("\nTesting Vector Store Deduplication...")
    try:
        store = VectorMemoryStore(collection_name="test_dedup")
        
        # Clear collection if possible or just use unique user_id
        user_id = "test_user_vec"
        
        text = "I love programming"
        meta = {"user_id": user_id, "source": "test"}
        
        # Add twice
        store.add_memory(text, meta)
        store.add_memory(text, meta)
        
        # Search/Count
        results = store.collection.get(where={"user_id": user_id})
        count = len(results['ids'])
        
        if count == 1:
            print("✅ Vector Deduplication Passed: 1 document found after 2 inserts.")
        else:
            print(f"❌ Vector Deduplication Failed: {count} documents found.")
            
    except Exception as e:
        print(f"⚠️ Vector Store Test Skipped/Failed: {e}")

if __name__ == "__main__":
    test_sqlite_deduplication()
    test_vector_deduplication()
