# reasoning/confidence.py

from typing import Dict


def compute_confidence(graph_delta: Dict) -> float:
    """
    Deterministic confidence scoring based on the extracted graph delta.
    A simple heuristic: if the extractor found edges, we assign a default
    high confidence. More complex logic can be added later (e.g., based on
    relation types, node types, etc.).
    """

    if graph_delta and graph_delta.get("edges"):
        # If we have edges, it means the extractor found a fact.
        # We can assign a baseline confidence score above MIN_CONFIDENCE_TO_STORE.
        return 0.75

    return 0.0
