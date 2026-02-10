# memory/sqlite_store.py

import sqlite3
from config import SQLITE_DB_PATH, DATA_DIR


class SQLiteMemoryStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(SQLITE_DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            edge_id TEXT PRIMARY KEY,
            src TEXT NOT NULL,
            dst TEXT NOT NULL,
            relation TEXT NOT NULL,
            confidence REAL,
            turn_id INTEGER,
            user_id TEXT,
            source_text TEXT
        )
        """)

        self.conn.commit()

    # -------------------------
    # Node operations
    # -------------------------
    def upsert_node(self, node_id: str, node_type: str):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT OR IGNORE INTO nodes (node_id, node_type)
        VALUES (?, ?)
        """, (node_id, node_type))
        self.conn.commit()

    # -------------------------
    # Edge operations
    # -------------------------
    def _compute_edge_id(self, user_id: str, src: str, relation: str, dst: str) -> str:
        """Generate a deterministic ID based on content to prevent duplicates."""
        import hashlib
        # Normalize content to lowercase to avoid case-sensitivity duplicates if desired,
        # but strict preservation is usually safer for names.
        content = f"{user_id}:{src}:{relation}:{dst}"
        return hashlib.md5(content.encode()).hexdigest()

    def insert_edge(self, edge: dict):
        cur = self.conn.cursor()
        
        # Ensure we have a deterministic ID
        if "edge_id" not in edge or not edge["edge_id"]:
            edge["edge_id"] = self._compute_edge_id(
                edge.get("user_id", "unknown"),
                edge["src"],
                edge["relation"],
                edge["dst"]
            )
        else:
            # Re-compute to force deduplication even if caller sent a random UUID
            # This enforces the content-addressable property
            edge["edge_id"] = self._compute_edge_id(
                edge.get("user_id", "unknown"),
                edge["src"],
                edge["relation"],
                edge["dst"]
            )

        cur.execute("""
        INSERT OR REPLACE INTO edges (
            edge_id, src, dst, relation,
            confidence, turn_id, user_id, source_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            edge["edge_id"],
            edge["src"],
            edge["dst"],
            edge["relation"],
            edge.get("confidence"),
            edge.get("turn_id"),
            edge.get("user_id"),
            edge.get("source_text"),
        ))
        self.conn.commit()

    # -------------------------
    # Retrieval (for fast pipe)
    # -------------------------
    def retrieve_edges_for_user(self, user_id: str):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT * FROM edges
        WHERE user_id = ?
        ORDER BY turn_id DESC
        """, (user_id,))
        return [dict(r) for r in cur.fetchall()]
