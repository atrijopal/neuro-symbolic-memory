# memory/neo4j_store.py

from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
import time

class Neo4jMemoryStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self._init_constraints()

    def close(self):
        self.driver.close()

    def _init_constraints(self):
        """Ensure uniqueness constraints exist for optimal performance."""
        with self.driver.session() as session:
            # Constraints for uniqueness
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")

    def upsert_node(self, node_id: str, node_type: str):
        """Insert or update a node."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (n:Entity {id: $id})
                SET n.type = $type, n.last_seen = timestamp()
                """,
                id=node_id, type=node_type
            )

    def insert_edge(self, edge: dict):
        """Insert an edge between two nodes with dynamic relationship type."""
        # Sanitize relation type (uppercase, underscores only)
        raw_rel = edge["relation"]
        clean_rel = "".join(c for c in raw_rel if c.isalnum() or c == "_").upper()
        if not clean_rel:
            clean_rel = "RELATED_TO"
            
        with self.driver.session() as session:
            # Note: We inject clean_rel directly because Cypher params don't work for types.
            # It is sanitized above to prevent injection.
            query = f"""
                MERGE (s:Entity {{id: $src}})
                MERGE (d:Entity {{id: $dst}})
                MERGE (s)-[r:{clean_rel}]->(d)
                ON CREATE SET 
                    r.confidence = $confidence,
                    r.turn_id = $turn_id,
                    r.user_id = $user_id,
                    r.source_text = $source_text,
                    r.first_seen = timestamp(),
                    r.last_updated = timestamp()
                ON MATCH SET 
                    r.confidence = r.confidence + (1.0 - r.confidence) * 0.2,
                    r.last_updated = timestamp(),
                    r.turn_id = $turn_id
            """
            session.run(
                query,
                src=edge["src"],
                dst=edge["dst"],
                confidence=edge.get("confidence", 0.75),
                turn_id=edge.get("turn_id"),
                user_id=edge.get("user_id"),
                source_text=edge.get("source_text")
            )

    def retrieve_context_with_activation(self, user_id: str, limit: int = 15) -> list:
        """
        Spreading Activation Retrieval (Cognitive Architecture)
        - Finds 'Anchor' nodes (Direct matches)
        - Spreads 'Energy' to 1-hop neighbors
        Using UNION for robustness.
        """
        with self.driver.session() as session:
            # 1. Direct Memories (High Confidence)
            # 2. Indirect Memories (Lower Confidence)
            # Changed [r:RELATION] to [r] to match ANY relationship type
            query = """
                MATCH (s)-[r]->(d)
                WHERE r.user_id = $user_id
                WITH s, r, d
                ORDER BY r.last_updated DESC
                LIMIT 5
                RETURN s.id as src, type(r) as relation, d.id as dst, r.confidence as score, 0 as depth, r.turn_id as turn_id, r.last_updated as last_updated
                
                UNION
                
                MATCH (s)-[r]->(d)
                WHERE r.user_id = $user_id
                WITH s, d
                ORDER BY r.last_updated DESC
                LIMIT 5
                WITH collect(s) + collect(d) as anchors
                UNWIND anchors as anchor
                MATCH (anchor)-[r2]-(neighbor)
                WHERE NOT neighbor IN anchors
                RETURN anchor.id as src, type(r2) as relation, neighbor.id as dst, (r2.confidence * 0.5) as score, 1 as depth, r2.turn_id as turn_id, r2.last_updated as last_updated
                ORDER BY score DESC
                LIMIT 10
            """
            result = session.run(query, user_id=user_id)
            
            return [
                {
                    "src": record["src"],
                    "relation": record["relation"],
                    "dst": record["dst"],
                    "score": record["score"],
                    "depth": record["depth"],
                    "turn_id": record["turn_id"],
                    "last_updated": record["last_updated"]
                }
                for record in result
            ]

    def retrieve_context(self, user_id: str, limit: int = 10) -> list:
        # Backward compatibility wrapper
        return self.retrieve_context_with_activation(user_id, limit)

    def get_related_nodes(self, entity_id: str) -> list:
        """Find immediate neighbors of an entity."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Entity {id: $id})-[r]-(d:Entity)
                RETURN d.id as neighbor, type(r) as relation
                LIMIT 20
                """,
                id=entity_id
            )
            return [{"neighbor": record["neighbor"], "relation": record["relation"]} for record in result]

    def wipe_database(self):
        """Delete all nodes and relationships."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
