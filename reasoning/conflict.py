# reasoning/conflict.py

from typing import Dict, List


def has_hard_conflict(
    new_memory: Dict,
    existing_memories: List[Dict]
) -> bool:
    """
    Detect hard conflicts.
    """

    for mem in existing_memories:
        if (
            mem["entity"] == new_memory["entity"]
            and mem["attribute"] == new_memory["attribute"]
            and mem["value"] != new_memory["value"]
            and mem["type"] == "constraint"
        ):
            return True

    return False
