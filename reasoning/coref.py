# reasoning/coref.py

from typing import List, Optional


AMBIGUOUS_PRONOUNS = {"it", "that", "this", "they", "them"}


def resolve_coreference(
    user_input: str,
    recent_turns: List[str]
) -> Optional[str]:
    """
    Resolve coreference using simple heuristics.
    Returns resolved text or None if ambiguous.
    """

    tokens = user_input.lower().split()

    # No pronouns → safe
    if not any(tok in AMBIGUOUS_PRONOUNS for tok in tokens):
        return user_input

    # No context → ambiguous
    if not recent_turns:
        return None

    # Try last turn as referent
    last_turn = recent_turns[-1].lower()

    # If multiple nouns in last turn → ambiguous
    words = last_turn.split()
    if len(words) > 6:
        return None

    # Simple resolution: replace pronoun with last turn
    resolved = user_input
    for p in AMBIGUOUS_PRONOUNS:
        resolved = resolved.replace(p, last_turn)

    return resolved
