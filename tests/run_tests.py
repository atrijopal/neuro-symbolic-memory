# tests/run_tests.py
import unittest
import sys
import os
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import test modules (we will create these next)
# from tests.test_unit_cognitive import CognitiveTestCase
# from tests.test_integration_rag import RagIntegrationTestCase

def run_all_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover all tests in the 'tests' directory
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
