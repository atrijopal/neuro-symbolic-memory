# memory/reset.py

import json
import shutil
import sqlite3
import time
from typing import Optional, Dict, Any
from pathlib import Path

from config import SQLITE_DB_PATH, CHROMA_DIR, DATA_DIR

# region agent log
_DEBUG_LOG_PATH = r"e:\NEUROHACK PROJECT\.cursor\debug.log"


def _dbg(hypothesisId: str, location: str, message: str, data: Optional[Dict[str, Any]] = None, runId: str = "wipe-v1") -> None:
    try:
        payload = {
            "id": f"log_{int(time.time() * 1000)}_{hypothesisId}",
            "timestamp": int(time.time() * 1000),
            "runId": runId,
            "hypothesisId": hypothesisId,
            "location": location,
            "message": message,
            "data": data or {},
        }
        Path(_DEBUG_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# endregion


def _reset_vector_client() -> None:
    # Avoid circular import by importing inside function where needed
    from memory.vector_store import reset_client
    reset_client()


def _wipe_sqlite_in_place(hypothesis_run: str) -> bool:
    """
    Clear SQLite tables without deleting the file. This avoids Windows file-lock issues (WinError 32).
    Returns True if wipe succeeded.
    """
    if not SQLITE_DB_PATH.exists():
        return True

    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        try:
            conn.execute("PRAGMA busy_timeout=2000;")
            conn.execute("DELETE FROM edges;")
            conn.execute("DELETE FROM nodes;")
            conn.commit()
            # Optional: reclaim space
            conn.execute("VACUUM;")
            conn.commit()
        finally:
            conn.close()
        _dbg("H1", "memory/reset.py:_wipe_sqlite_in_place", "sqlite_wipe_in_place_ok", {"db": str(SQLITE_DB_PATH), "mode": hypothesis_run})
        return True
    except Exception as e:
        _dbg("H1", "memory/reset.py:_wipe_sqlite_in_place", "sqlite_wipe_in_place_failed", {"db": str(SQLITE_DB_PATH), "mode": hypothesis_run, "error": repr(e)})
        return False


def _wipe_chroma_best_effort(hypothesis_run: str) -> bool:
    """
    Best-effort wipe for Chroma persistence:
    - reset in-process client to drop file handles
    - try delete directory
    - if locked, try deleting known collections via Chroma API
    Never raises.
    """
    try:
        _reset_vector_client()
    except Exception as e:
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "reset_vector_client_failed", {"error": repr(e), "mode": hypothesis_run})

    if not CHROMA_DIR.exists():
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_dir_missing", {"dir": str(CHROMA_DIR), "mode": hypothesis_run})
        return True

    try:
        shutil.rmtree(CHROMA_DIR)
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_rmtree_ok", {"dir": str(CHROMA_DIR), "mode": hypothesis_run})
        return True
    except Exception as e:
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_rmtree_failed", {"dir": str(CHROMA_DIR), "mode": hypothesis_run, "error": repr(e)})

    # Fallback: try to delete collections (may still fail if locked)
    deleted_any = False
    try:
        import chromadb  # type: ignore
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        for name in ("neuro_symbolic_memory", "memories"):
            try:
                client.delete_collection(name=name)
                _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_delete_collection_ok", {"collection": name, "mode": hypothesis_run})
                deleted_any = True
            except Exception as e:
                _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_delete_collection_failed", {"collection": name, "mode": hypothesis_run, "error": repr(e)})
    except Exception as e:
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_client_failed", {"dir": str(CHROMA_DIR), "mode": hypothesis_run, "error": repr(e)})
        return False

    if deleted_any:
        return True

    # If nothing was deleted because collections don't exist, consider it wiped if there are no collections.
    try:
        cols = client.list_collections()
        col_names = [getattr(c, "name", None) for c in cols]  # tolerate different chromadb versions
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_list_collections", {"mode": hypothesis_run, "collections": col_names})
        return len(cols) == 0
    except Exception as e:
        _dbg("H2", "memory/reset.py:_wipe_chroma_best_effort", "chroma_list_collections_failed", {"mode": hypothesis_run, "error": repr(e)})
        return False


def _wipe_neo4j() -> bool:
    """
    Connects to Neo4j and deletes all nodes and relationships.
    Returns True if successful.
    """
    try:
        from memory.neo4j_store import Neo4jMemoryStore
        store = Neo4jMemoryStore()
        store.wipe_database()
        store.close()
        return True
    except Exception as e:
        _dbg("H3", "memory/reset.py:_wipe_neo4j", "neo4j_wipe_failed", {"error": repr(e)})
        return False


def wipe_all_memory(ram_context=None) -> dict:
    """
    Delete all stored memory at once.

    Important (Windows): Deleting the SQLite file can fail with WinError 32 if another process has it open.
    We therefore prefer an in-place wipe (DELETE FROM tables) and only unlink the DB file if possible.
    """
    hypothesis_run = "wipe_all_memory"
    _dbg("H3", "memory/reset.py:wipe_all_memory", "enter", {
        "sqlite_exists": SQLITE_DB_PATH.exists(),
        "chroma_exists": CHROMA_DIR.exists(),
        "has_ram_context": ram_context is not None,
    })

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # --- SQLite wipe ---
    sqlite_wiped = False
    if SQLITE_DB_PATH.exists():
        # Try unlink first (fast), but fall back to in-place wipe if locked
        try:
            SQLITE_DB_PATH.unlink()
            sqlite_wiped = True
            _dbg("H1", "memory/reset.py:wipe_all_memory", "sqlite_unlink_ok", {"db": str(SQLITE_DB_PATH), "mode": hypothesis_run})
        except OSError as e:
            _dbg("H1", "memory/reset.py:wipe_all_memory", "sqlite_unlink_failed", {"db": str(SQLITE_DB_PATH), "mode": hypothesis_run, "error": repr(e)})
            sqlite_wiped = _wipe_sqlite_in_place(hypothesis_run)
    else:
        sqlite_wiped = True # Nothing to wipe

    # --- Neo4j wipe ---
    neo4j_wiped = _wipe_neo4j()

    # --- Chroma wipe (best effort; returns bool) ---
    chroma_wiped = _wipe_chroma_best_effort("cli_reset")

    # --- RAM Context ---
    # In a real app this might need an API call if running in separate process
    # Here we just print a reminder if used as CLI
    if __name__ == "__main__":
        pass

    _dbg("H3", "memory/reset.py:wipe_all_memory", "exit", {"neo4j_wiped": neo4j_wiped, "chroma_wiped": chroma_wiped})

    if not neo4j_wiped:
        print("WARNING: Neo4j Connected Failed. Is the database running?")

    if not chroma_wiped:
        print("WARNING: ChromaDB wipe failed (likely locked). Close other running processes and retry.")

    return {"sqlite_wiped": sqlite_wiped, "chroma_wiped": chroma_wiped}
