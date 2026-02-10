# memory/ram_context.py

from collections import deque
from typing import Dict, List


class RAMContext:
    """
    In-memory short-term context.
    Stores last N turns per session.
    """

    def __init__(self, maxlen: int = 8):
        self.maxlen = maxlen
        self._store: Dict[str, deque] = {}

    def add(self, session_id: str, text: str) -> None:
        """
        Add a new turn to RAM context.
        """
        if session_id not in self._store:
            self._store[session_id] = deque(maxlen=self.maxlen)

        self._store[session_id].append(text)

    def get(self, session_id: str) -> List[str]:
        """
        Get recent turns for a session.
        Returns empty list if none exist.
        """
        if session_id not in self._store:
            return []

        return list(self._store[session_id])

    def clear(self) -> None:
        """Clear all in-memory turns for all sessions."""
        self._store.clear()
