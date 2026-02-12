#!/usr/bin/env python3
"""
Comprehensive test suite for logic bomb feature.
Tests extraction, contradiction detection, and end-to-end flow.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from reasoning.extractor import extract_graph_delta
from reasoning.omniscience import detect_contradiction
import time

def test_extraction():
    """Test that extraction produces consistent ORIGIN_FROM relations."""
    print("=" * 60)
    print("TEST 1: EXTRACTION QUALITY")
    print("=" * 60)
    
    test_cases = [
        ("i am from kerala", "ORIGIN_FROM", "Kerala"),
        ("i am from up", "ORIGIN_FROM", "UP"),
        ("i'm from delhi", "ORIGIN_FROM", "Delhi"),
        ("my mom's name is sita", "MOTHER_NAME", "Sita"),
        ("my dad's name is ram", "FATHER_NAME", "Ram"),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_rel, expected_dst in test_cases:
        print(f"\nInput: '{text}'")
        result = extract_graph_delta(text)
        
        if not result or not result.get("edges"):
            print(f"  [FAIL] No edges extracted")
            failed += 1
            continue
            
        edge = result["edges"][0]
        relation = edge.get("relation", "")
        dst = edge.get("dst", "")
        
        print(f"  Extracted: relation={relation}, dst={dst}")
        
        if relation == expected_rel and dst.lower() == expected_dst.lower():
            print(f"  [PASS]")
            passed += 1
        else:
            print(f"  [FAIL] Expected relation={expected_rel}, dst={expected_dst}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION TEST: {passed}/{len(test_cases)} passed")
    print(f"{'='*60}\n")
    
    return failed == 0


def test_contradiction_detection():
    """Test omniscience LLM contradiction detection."""
    print("=" * 60)
    print("TEST 2: CONTRADICTION DETECTION")
    print("=" * 60)
    
    test_cases = [
        # (new_fact, existing_fact, should_contradict)
        (
            {"src": "User", "dst": "UP", "relation": "ORIGIN_FROM"},
            {"src": "User", "dst": "Kerala", "relation": "ORIGIN_FROM"},
            True,  # Different locations contradict
        ),
        (
            {"src": "User", "dst": "Sita", "relation": "MOTHER_NAME"},
            {"src": "User", "dst": "Devi", "relation": "MOTHER_NAME"},
            True,  # Different mother names contradict
        ),
        (
            {"src": "User", "dst": "unknown_location", "relation": "origin"},
            {"src": "User", "dst": "Kerala", "relation": "ORIGIN_FROM"},
            False,  # Question doesn't contradict
        ),
        (
            {"src": "User", "dst": "greeting_phrase", "relation": "verb_phrase"},
            {"src": "User", "dst": "Kerala", "relation": "ORIGIN_FROM"},
            False,  # Greeting doesn't contradict location
        ),
    ]
    
    passed = 0
    failed = 0
    
    for new_fact, old_fact, expected_contradiction in test_cases:
        print(f"\nComparing:")
        print(f"  New: {new_fact}")
        print(f"  Old: {old_fact}")
        print(f"  Expected: {'CONTRADICTION' if expected_contradiction else 'NO CONTRADICTION'}")
        
        is_contradiction = detect_contradiction(new_fact, old_fact)
        
        if is_contradiction == expected_contradiction:
            print(f"  [PASS] Got: {'CONTRADICTION' if is_contradiction else 'NO CONTRADICTION'}")
            passed += 1
        else:
            print(f"  [FAIL] Got: {'CONTRADICTION' if is_contradiction else 'NO CONTRADICTION'}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"CONTRADICTION TEST: {passed}/{len(test_cases)} passed")
    print(f"{'='*60}\n")
    
    return failed == 0


def test_end_to_end():
    """Test full end-to-end logic bomb flow."""
    print("=" * 60)
    print("TEST 3: END-TO-END LOGIC BOMB")
    print("=" * 60)
    
    from memory.ram_context import RAMContext
    from memory.reset import wipe_all_memory
    from fast_pipe import fast_pipe
    
    session_id = "test_user"
    ram_context = RAMContext()
    
    # Wipe memory
    print("\n[STEP 1] Wiping memory...")
    wipe_all_memory(ram_context=ram_context)
    print("[PASS] Memory wiped")
    
    # First fact: from kerala
    print("\n[STEP 2] User: 'i am from kerala'")
    ram_context.add(session_id, "i am from kerala")
    result1 = fast_pipe("i am from kerala", session_id, ram_context)
    print(f"Response: {result1['response']}")
    print(f"Latency: {result1['latency_ms']}ms")
    
    # Wait for slow_pipe to store
    print("[WAIT] Allowing slow_pipe to complete...")
    time.sleep(3)
    
    # Contradictory fact: from up
    print("\n[STEP 3] User: 'i am from up' (should be blocked)")
    ram_context.add(session_id, "i am from up")
    result2 = fast_pipe("i am from up", session_id, ram_context)
    print(f"Response: {result2['response']}")
    print(f"Latency: {result2['latency_ms']}ms")
    
    # Check if blocked
    if "contradict" in result2['response'].lower():
        print("\n[PASS] Logic bomb fired correctly!")
        return True
    else:
        print("\n[FAIL] Logic bomb did NOT fire!")
        print("Expected response containing 'contradict'")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("COMPREHENSIVE LOGIC BOMB TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Run all tests
        test1_pass = test_extraction()
        time.sleep(1)  # Brief pause between tests
        
        test2_pass = test_contradiction_detection()
        time.sleep(1)
        
        test3_pass = test_end_to_end()
        
        # Summary
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        print(f"Test 1 (Extraction):      {'[PASS]' if test1_pass else '[FAIL]'}")
        print(f"Test 2 (Contradiction):   {'[PASS]' if test2_pass else '[FAIL]'}")
        print(f"Test 3 (End-to-End):      {'[PASS]' if test3_pass else '[FAIL]'}")
        print("=" * 60)
        
        if test1_pass and test2_pass and test3_pass:
            print("\n[SUCCESS] All tests passed!")
            sys.exit(0)
        else:
            print("\n[FAILURE] Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
