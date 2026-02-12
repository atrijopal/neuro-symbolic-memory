#!/usr/bin/env python3
"""Quick test to check extraction of location facts."""
import sys
sys.path.insert(0, 'e:\\NEUROHACK PROJECT\\neuro_symbolic_memory')

from reasoning.extractor import extract_graph_delta

# Test inputs
tests =  [
    ("i am from kerala", "ORIGIN_FROM"),
    ("i am from up", "ORIGIN_FROM"),
    ("my mom's name is sita", "MOTHER_NAME"),
]

print("Testing extraction...")
for text, expected_relation in tests:
    print(f"\nInput: '{text}'")
    result = extract_graph_delta(text)
    if result and result.get("edges"):
        edge = result["edges"][0]
        relation = edge.get("relation")
        print(f"  Extracted: {relation}")
        if relation == expected_relation:
            print(f"  [PASS] Correct!")
        else:
            print(f"  [FAIL] Expected {expected_relation}")
    else:
        print(f"  [FAIL] No edges extracted!")
