# evaluation/metrics.py
from typing import Dict, Any, List, Tuple

def _normalize_edge(edge: Dict) -> Tuple[str, str, str]:
    """Normalizes an edge into a comparable tuple, handling variations."""
    src = str(edge.get("src", "")).lower().replace("my", "user").replace("i", "user")
    dst = str(edge.get("dst", "")).lower()
    relation = str(edge.get("relation", "")).lower()
    # Further normalization could be added here, e.g., for verb forms
    return (src, relation, dst)

def evaluate_store_turn(turn_eval: Dict, agent_output: Dict) -> Dict[str, Any]:
    """Evaluates a 'store' turn for extraction accuracy."""
    
    expected_edges_raw = turn_eval.get("expected_edges", [])
    if not expected_edges_raw:
        return {"passed": True, "reason": "No expected edges to check."}

    extracted_graph = agent_output.get("newly_extracted_graph")
    if not extracted_graph or not extracted_graph.get("edges"):
        return {"passed": False, "reason": "Agent extracted no facts."}

    expected_set = {_normalize_edge(e) for e in expected_edges_raw}
    extracted_set = {_normalize_edge(e) for e in extracted_graph["edges"]}
    
    # Recall: Did we find all the facts we expected?
    missing_facts = expected_set - extracted_set
    if missing_facts:
        return {
            "passed": False,
            "reason": f"Agent failed to extract expected facts: {list(missing_facts)}",
            "details": {"expected": list(expected_set), "extracted": list(extracted_set)}
        }
    
    # Precision: Did the agent extract extra, incorrect facts?
    # For simplicity, we'll focus on recall for now, as it's more critical for memory.
    # A full precision check would require knowing ALL possible correct facts.
    
    return {
        "passed": True,
        "reason": "Agent successfully extracted all expected facts.",
        "details": {"expected": list(expected_set), "extracted": list(extracted_set)}
    }

def evaluate_retrieve_turn(turn_eval: Dict, agent_output: Dict) -> Dict[str, Any]:
    """Evaluates a 'retrieve' turn for response accuracy."""
    
    expected_substrings = turn_eval.get("expected_response_contains", [])
    if not expected_substrings:
        return {"passed": True, "reason": "No expected response content to check."}
        
    response = agent_output.get("response", "").lower()
    
    for sub in expected_substrings:
        if sub.lower() not in response:
            return {
                "passed": False,
                "reason": f"Response did not contain expected substring '{sub}'.",
                "details": {"response": agent_output.get("response"), "expected": sub}
            }
            
    return {"passed": True, "reason": "Response contained all expected substrings."}

def evaluate_none_turn(turn_eval: Dict, agent_output: Dict) -> Dict[str, Any]:
    """Evaluates a 'none' turn (e.g., chit-chat)."""
    # We check if it *incorrectly* extracts facts.
    extracted_graph = agent_output.get("newly_extracted_graph")
    if extracted_graph and extracted_graph.get("edges"):
        return {
            "passed": False,
            "reason": "Agent incorrectly extracted facts from simple chit-chat.",
            "details": {"extracted_edges": extracted_graph["edges"]}
        }
    return {"passed": True, "reason": "Handled chit-chat correctly."}