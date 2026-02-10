# diagnostics/logger.py

import time
from typing import Any


def log_event(event: str, **kwargs: Any) -> None:
    """
    Lightweight structured logger.
    Never raises. Safe to call anywhere.
    """

    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        details = " ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"[{timestamp}] {event} {details}")
    except Exception:
        # Logging must never crash the system
        pass
