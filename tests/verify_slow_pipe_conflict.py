import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import slow_pipe to test
from slow_pipe import slow_pipe

def verify_slow_pipe_conflict():
    print("\n[TEST] Testing Slow Pipe 'Logic Bomb' Handling...")

    # Mock inputs
    user_input = "I hate nature"
    session_id = "test_session"
    ram_context = {}
    
    # Mock Graph Delta that WOULD cause a conflict
    mock_graph_delta = {
        "nodes": [{"id": "User", "type": "Person"}, {"id": "Nature", "type": "Concept"}],
        "edges": [{"src": "User", "dst": "Nature", "relation": "HATES", "confidence": 0.9}]
    }

    # We need to mock:
    # 1. extract_graph_delta (to return our mock data)
    # 2. detect_contradiction (to FORCE a conflict result)
    # 3. log_event (to verify it aborts)
    # 4. Neo4jMemoryStore (to ensure NO database writes happen)

    with patch('reasoning.extractor.extract_graph_delta', return_value=mock_graph_delta), \
         patch('reasoning.omniscience.detect_contradiction', return_value=True), \
         patch('slow_pipe.log_event') as mock_logger, \
         patch('memory.neo4j_store.Neo4jMemoryStore') as mock_store_cls:

        # Run the pipe
        print("   Running slow_pipe with forced contradiction...")
        slow_pipe(user_input, session_id, ram_context)

        # assertions
        # 1. It should NOT have opened the store
        mock_store_cls.assert_not_called()
        print("[+] Store check: Neo4j was NOT accessed (Good).")

        # 2. It should have logged ABORT
        # Look for a call with "SLOW_PIPE_ABORT" and reason="logic_bomb_contradiction"
        found_abort = False
        for call in mock_logger.mock_calls:
            # call.args[0] is the event name, call.kwargs has 'reason'
            if len(call.args) > 0 and call.args[0] == "SLOW_PIPE_ABORT":
                if call.kwargs.get('reason') == "logic_bomb_contradiction":
                    found_abort = True
                    break
        
        if found_abort:
            print("[+] Log check: Correctly aborted with 'logic_bomb_contradiction'.")
        else:
            print("[-] Log check: Did NOT log expected abort message.")
            print(f"   Calls were: {mock_logger.mock_calls}")

if __name__ == "__main__":
    verify_slow_pipe_conflict()
