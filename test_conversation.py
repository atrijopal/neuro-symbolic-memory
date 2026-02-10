#!/usr/bin/env python3
"""
Test conversation script to simulate chatting and identify issues.
Run: python test_conversation.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from memory.ram_context import RAMContext
from fast_pipe import fast_pipe
from memory.reset import wipe_all_memory
import time


def simulate_conversation():
    """Simulate a conversation to test the system."""
    print("=" * 70)
    print("Simulated Conversation Test")
    print("=" * 70)
    print()
    
    # Start fresh
    print("Step 1: Wiping all memory...")
    wipe_all_memory()
    print("✓ Memory wiped\n")
    
    session_id = "test_user"
    ram_context = RAMContext()
    
    # Test conversation
    test_turns = [
        ("hi jay from tamil nadu", "Should extract location fact"),
        ("my moms name is radha", "Should extract mother's name"),
        ("what is my mom's name?", "Should recall Radha"),
        ("I love pizza", "Should extract preference"),
        ("what do I like?", "Should recall pizza"),
    ]
    
    print("Step 2: Running test conversation...\n")
    
    for i, (user_input, expected) in enumerate(test_turns, 1):
        print(f"Turn {i}: User> {user_input}")
        print(f"  Expected: {expected}")
        
        ram_context.add(session_id, user_input)
        
        try:
            result = fast_pipe(
                user_input=user_input,
                session_id=session_id,
                ram_context=ram_context,
            )
            print(f"  Assistant> {result['response']}")
            
            # Wait a bit for slow_pipe to complete
            if i < len(test_turns):
                time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 70)
    print("Test completed. Check logs above for any issues.")
    print("=" * 70)


if __name__ == "__main__":
    simulate_conversation()
