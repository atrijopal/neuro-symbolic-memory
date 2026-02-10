#!/usr/bin/env python3
"""
Standalone script to delete all memory (SQLite + Chroma + RAM).
Usage: python del.py
"""

import json
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import
sys.path.insert(0, str(Path(__file__).parent))

from memory.reset import wipe_all_memory
from config import SQLITE_DB_PATH, CHROMA_DIR

# region agent log
_DEBUG_LOG_PATH = r"e:\NEUROHACK PROJECT\.cursor\debug.log"


def _dbg(hypothesisId: str, location: str, message: str, data=None, runId: str = "del-v1") -> None:
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


def main():
    print("=" * 60)
    print("Memory Deletion Script")
    print("=" * 60)
    print()
    print("This will delete:")
    print(f"  - SQLite database: {SQLITE_DB_PATH}")
    print(f"  - Chroma vector store: {CHROMA_DIR}")
    print("  - All stored memories and embeddings")
    print()
    
    response = input("Are you sure you want to delete ALL memory? (yes/no): ").strip().lower()
    
    if response not in ("yes", "y"):
        print("Cancelled. No memory was deleted.")
        return
    
    print("\nDeleting all memory...")
    
    try:
        _dbg("H5", "del.py:main", "wipe_start", {"sqlite": str(SQLITE_DB_PATH), "chroma": str(CHROMA_DIR)})
        result = wipe_all_memory()
        _dbg("H5", "del.py:main", "wipe_ok", {})
        print("✓ Successfully deleted all memory!")
        print(f"  - sqlite_wiped: {result.get('sqlite_wiped')}")
        print(f"  - chroma_wiped: {result.get('chroma_wiped')}")
        print("\nThe system will start fresh on the next run.")
    except Exception as e:
        _dbg("H5", "del.py:main", "wipe_failed", {"error": repr(e)})
        print(f"✗ Error during deletion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
