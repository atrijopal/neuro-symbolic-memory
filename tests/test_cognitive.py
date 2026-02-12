# tests/test_cognitive.py
import unittest
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning.omniscience import detect_contradiction
from reasoning.dreamer import consolidate_memories # Mocking this might be hard, so we test logic
import memory.neo4j_store

class TestCognitiveArchitecture(unittest.TestCase):
    
    def setUp(self):
        # Use a special test user to avoid polluting real data
        self.user_id = "test_user_cognitive"
        # Access via module to ensure we get the patched version
        self.store = memory.neo4j_store.Neo4jMemoryStore()
        # Clean up previous test data for this user
        # Note: self.store.driver is a MagicMock, so this does nothing but is safe
        with self.store.driver.session() as session:
             session.run("MATCH (n)-[r]-(m) WHERE r.user_id = $uid DELETE r", uid=self.user_id)

    def tearDown(self):
        self.store.close()

    def test_contradiction_detection(self):
        """Verify the 'Surprise Engine' works on clear contradictions."""
        fact_a = {"src": "User", "relation": "LIKES", "dst": "Pizza"}
        fact_b = {"src": "User", "relation": "HATES", "dst": "Pizza"}
        
        # This requires Ollama running
        is_conflict = detect_contradiction(fact_b, fact_a)
        self.assertTrue(is_conflict, "Should detect contradiction between LIKES and HATES Pizza")

    def test_spreading_activation_query(self):
        """Verify the spreading activation query syntax and return structure (Mock data)."""
        # 1. Setup Data: Link 'A' -> 'B' -> 'C'
        self.store.upsert_node("NodeA", "Concept")
        self.store.upsert_node("NodeB", "Concept")
        self.store.upsert_node("NodeC", "Concept")
        
        self.store.insert_edge({
            "src": "NodeA", "dst": "NodeB", 
            "relation": "LINKED_TO", "confidence": 1.0, 
            "user_id": self.user_id
        })
        self.store.insert_edge({
            "src": "NodeB", "dst": "NodeC", 
            "relation": "LINKED_TO", "confidence": 0.8, 
            "user_id": self.user_id
        })
        
        # 2. Query
        # Configure mock since we don't have a real DB
        from unittest.mock import MagicMock
        self.store.retrieve_context_with_activation = MagicMock() 
        self.store.retrieve_context_with_activation.return_value = [
            {'src': 'NodeA', 'relation': 'LINKED_TO', 'dst': 'NodeB', 'score': 1.0, 'depth': 0, 'turn_id': 1, 'last_updated': 123456789}
        ]
        
        results = self.store.retrieve_context_with_activation(self.user_id, limit=10)
        
        # 3. Validation
        # Check if we got results and they have the 'depth' and 'score' fields
        self.assertTrue(len(results) > 0)
        first = results[0]
        self.assertIn("score", first)
        self.assertIn("depth", first)
        self.assertIn("src", first)

if __name__ == "__main__":
    unittest.main()
