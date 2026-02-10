#!/usr/bin/env python3
"""
Evaluation runner for the Neuro-Symbolic Memory agent.

This script runs a series of simulated conversations from a dataset
and evaluates the agent's performance on fact extraction and retrieval.
"""

import json
import sys
import time
from pathlib import Path
from tqdm import tqdm

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.ram_context import RAMContext
from fast_pipe import fast_pipe
from memory.reset import wipe_all_memory
from evaluation.metrics import (
    evaluate_store_turn,
    evaluate_retrieve_turn,
    evaluate_none_turn,
)

DATASET_PATH = Path(__file__).parent / "dataset.json"

def _print_graph_visualization(graph_delta: dict):
    """Prints a simple ASCII visualization of the extracted knowledge graph."""
    if not graph_delta or not graph_delta.get("edges"):
        return

    print("  [Knowledge Graph Extracted]")
    nodes = graph_delta.get("nodes", [])
    edges = graph_delta.get("edges", [])

    if nodes:
        node_ids = {n.get('id', 'N/A') for n in nodes}
        print(f"    Nodes: {', '.join(sorted(list(node_ids)))}")

    if edges:
        print("    Edges:")
        for edge in edges:
            print(f"      ({edge.get('src', '?')}) --[{edge.get('relation', '...')}]--> ({edge.get('dst', '?')})")
    print() # Add a newline for spacing

def run_evaluation():
    """Main function to run the evaluation suite."""
    
    print("=" * 80)
    print("Neuro-Symbolic Memory Agent - Evaluation Suite")
    print("=" * 80)

    # 1. Load Dataset
    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        sys.exit(1)
    
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    print(f"✓ Loaded dataset with {len(dataset)} conversations.\n")

    total_turns = 0
    passed_turns = 0
    failed_turns_details = []

    # 2. Run evaluation for each conversation
    for conversation in dataset:
        conv_id = conversation.get("conversation_id", "unknown_convo")
        print(f"\n--- Running Conversation: {conv_id} ---")
        print(f"Description: {conversation.get('description', 'N/A')}")
        
        # Reset memory for each new conversation
        wipe_all_memory()
        session_id = f"eval_{conv_id}"
        ram_context = RAMContext()
        
        # Use tqdm for a progress bar over the turns
        for turn in tqdm(conversation.get("turns", []), desc=f"  {conv_id}"):
            total_turns += 1
            user_input = turn["user_input"]
            eval_spec = turn.get("eval", {})
            eval_type = eval_spec.get("type", "none")

            ram_context.add(session_id, user_input)

            agent_output = fast_pipe(
                user_input=user_input,
                session_id=session_id,
                ram_context=ram_context,
            )
            
            # Visualize the extracted graph for this turn
            _print_graph_visualization(agent_output.get("newly_extracted_graph"))

            result = {}
            if eval_type == "store":
                result = evaluate_store_turn(eval_spec, agent_output)
            elif eval_type == "retrieve":
                result = evaluate_retrieve_turn(eval_spec, agent_output)
            elif eval_type == "none":
                result = evaluate_none_turn(eval_spec, agent_output)
            else:
                result = {"passed": True, "reason": "Unknown eval type, skipping."}

            if result["passed"]:
                passed_turns += 1
            else:
                failed_turns_details.append({
                    "conversation_id": conv_id,
                    "turn_id": turn.get("turn_id"),
                    "user_input": user_input,
                    "agent_response": agent_output.get("response"),
                    "failure_reason": result["reason"],
                    "details": result.get("details", {})
                })
            
            time.sleep(1)

    # 3. Print Summary Report
    print("\n\n" + "=" * 80)
    print("Evaluation Summary")
    print("=" * 80)

    pass_rate = (passed_turns / total_turns) * 100 if total_turns > 0 else 0
    
    print(f"Total Turns: {total_turns}, Passed: {passed_turns}, Failed: {len(failed_turns_details)}")
    print(f"Success Rate: {pass_rate:.2f}%")

    if failed_turns_details:
        print("\n--- Failed Turns Details ---")
        for i, failure in enumerate(failed_turns_details, 1):
            print(f"\n{i}. Conv: {failure['conversation_id']} (Turn {failure['turn_id']}) | Input: '{failure['user_input']}'")
            print(f"   Reason: {failure['failure_reason']}")
            if failure['details']:
                print(f"   Details: {json.dumps(failure['details'], indent=2)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_evaluation()