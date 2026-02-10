#!/usr/bin/env python3
"""
Test script to verify Phi/Gemma extraction works correctly.
Run: python test_extractor.py
"""

import sys
from reasoning.extractor import extract_graph_delta
from config import EXTRACTION_MODEL, OLLAMA_BASE_URL
import requests


def test_model_available():
    """Check if the extraction model is available."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            if EXTRACTION_MODEL in model_names:
                print(f"OK Model '{EXTRACTION_MODEL}' is available")
                return True
            else:
                print(f"FAIL Model '{EXTRACTION_MODEL}' not found. Available: {model_names}")
                return False
    except Exception as e:
        print(f"FAIL Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
        return False


def test_extraction(test_cases):
    """Test extraction on multiple inputs."""
    print(f"\n{'='*60}")
    print(f"Testing extraction with {EXTRACTION_MODEL}")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0

    for i, (input_text, expected_has_edges) in enumerate(test_cases, 1):
        print(f"Test {i}: {input_text}")
        print("-" * 60)
        
        result = extract_graph_delta(input_text)
        
        if result is None:
            if not expected_has_edges:
                print("OK PASS: Correctly returned None (no facts)")
                passed += 1
            else:
                print("FAIL: Expected edges but got None")
                failed += 1
        else:
            edges = result.get("edges", [])
            nodes = result.get("nodes", [])
            
            if expected_has_edges:
                if edges:
                    print(f"OK PASS: Extracted {len(edges)} edge(s), {len(nodes)} node(s)")
                    for edge in edges:
                        print(f"  Edge: {edge.get('src')} --[{edge.get('relation')}]--> {edge.get('dst')}")
                    passed += 1
                else:
                    print("FAIL: Expected edges but got empty list")
                    failed += 1
            else:
                print(f"WARN: Got edges when expected None: {edges}")
                failed += 1
        
        print()
    
    print(f"{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")
    
    return failed == 0


def main():
    print("Phi/Gemma Extractor Test Suite")
    print("=" * 60)
    
    # Check model availability
    if not test_model_available():
        print("\nWARN: Please ensure Ollama is running and the model is pulled.")
        print(f"  Run: ollama pull {EXTRACTION_MODEL}")
        #sys.exit(1)
    
    # Test cases: (input_text, should_have_edges)
    test_cases = [
        ("I love pizza", True),
        ("my moms name is radha", True),
        ("I live in Chennai", True),
        ("hello", False),
        ("what is the weather?", False),
        ("My mother's name is Priya", True),
        ("I am from Tamil Nadu", True),
        ("hi jay from tamil nadu", True),  # Should extract location fact
        ("thanks", False),
    ]
    
    success = test_extraction(test_cases)
    
    if success:
        print("OK All tests passed!")
        sys.exit(0)
    else:
        print("FAIL: Some tests failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
