import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.neo4j_store import Neo4jMemoryStore # type: ignore
from reasoning.dreamer import _prune_old_edges # type: ignore

def verify_pruning():
    store = Neo4jMemoryStore()
    user_id = "test_dream_user"

    print("\n[+] Setting up test scenario...")
    # 1. Clear previous test data
    with store.driver.session() as session:
        session.run("MATCH (n)-[r]-(m) WHERE r.user_id = $uid DELETE r, n, m", uid=user_id)

    # 2. Insert 5 dummy facts (Simulation of clutter)
    facts = []
    print("   Creating 5 redundant edges...")
    for i in range(5):
        store.insert_edge({
            "src": "User",
            "dst": f"Fact_{i}",
            "relation": "KNOWS",
            "confidence": 1.0,
            "user_id": user_id,
            "source_text": f"Fact {i}"
        })
    
    # 3. Retrieve them to get their IDs
    with store.driver.session() as session:
        result = session.run(
            """
            MATCH (n:Entity {id: 'User'})-[r]-(m)
            WHERE r.user_id = $uid
            RETURN elementId(r) as edge_id
            """,
            uid=user_id
        )
        edge_data = [{"edge_id": record["edge_id"]} for record in result]
    
    initial_count = len(edge_data)
    print(f"   Initial Edge Count: {initial_count}")
    if initial_count != 5:
        print("[-] Setup failed. Edges not created.")
        return

    # 4. Run the PRUNE function
    print("\n[CUT] Executing _prune_old_edges()...")
    try:
        _prune_old_edges(store, edge_data)
    except Exception as e:
        print(f"[-] Pruning function crashed: {e}")
        return

    # 5. Verify they are gone
    with store.driver.session() as session:
        result = session.run(
            """
            MATCH (n:Entity {id: 'User'})-[r]-(m)
            WHERE r.user_id = $uid
            RETURN count(r) as count
            """,
            uid=user_id
        )
        final_count = result.single()["count"]

    print(f"   Final Edge Count: {final_count}")

    if final_count == 0:
        print("\n[+] SUCCESS: All redundant edges were pruned.")
    else:
        print(f"\n[-] FAILURE: {final_count} edges remain.")

    store.close()

if __name__ == "__main__":
    verify_pruning()
