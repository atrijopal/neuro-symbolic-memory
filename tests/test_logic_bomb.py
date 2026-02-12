#!/usr/bin/env python3
"""
Test script to verify logic bomb catches contradictions before response.
"""

import sys
sys.path.insert(0, 'e:\\NEUROHACK PROJECT\\neuro_symbolic_memory')

from memory.ram_context import RAMContext
from memory.reset import wipe_all_memory
from fast_pipe import fast_pipe
import time

def test_logic_bomb():
    print("=" * 60)
    print("LOGIC BOMB TEST - Location Contradiction")
    print("=" * 60)
    
    # Setup
    session_id = "test_user"
    ram_context = RAMContext()
    
    # Step 1: Wipe memory
    print("\n[TEST] Wiping all memory...")
    wipe_all_memory(ram_context=ram_context)
    print("[PASS] Memory wiped\n")
    
    # Step 2: Introduction
    print("[TEST] User: hi i am bhusan")
    ram_context.add(session_id, "hi i am bhusan")
    result1 = fast_pipe("hi i am bhusan", session_id, ram_context)
    print(f"Assistant: {result1['response']}")
    print(f"Latency: {result1['latency_ms']}ms\n")
    
    # Give slow_pipe time to complete
    time.sleep(2)
    
    # Step 3: First location (should work)
    print("[TEST] User: i am from kerala")
    ram_context.add(session_id, "i am from kerala")
    result2 = fast_pipe("i am from kerala", session_id, ram_context)
    print(f"Assistant: {result2['response']}")
    print(f"Latency: {result2['latency_ms']}ms\n")
    
    # Give slow_pipe time to complete
    time.sleep(2)
    
    # Step 4: Contradictory location (should be BLOCKED by logic bomb)
    print("[TEST] User: i am from up")
    ram_context.add(session_id, "i am from up")
    result3 = fast_pipe("i am from up", session_id, ram_context)
    print(f"Assistant: {result3['response']}")
    print(f"Latency: {result3['latency_ms']}ms\n")
    
    # Verify
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    if "contradict" in result3['response'].lower():
        print("[PASS] Logic bomb fired correctly!")
        print(f"   Blocked response: '{result3['response']}'")
        return True
    else:
        print("[FAIL] Logic bomb did NOT fire!")
        print(f"   Got response: '{result3['response']}'")
        print("\nDEBUG: Check logs above for LOGIC_BOMB events")
        return False

if __name__ == "__main__":
    try:
        success = test_logic_bomb()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
