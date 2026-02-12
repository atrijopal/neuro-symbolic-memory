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
    
    if not result.wasSuccessful():
        return False
        
    # --- Custom Verification Scripts ---
    import subprocess
    
    scripts = [
        "verify_neo4j.py",
        "verify_spreading_activation.py",
        "verify_slow_pipe_conflict.py",
        "verify_dream_pruning.py",
        "verify_performance.py"
    ]
    
    print("\n" + "="*40)
    print("[FAST] Running Custom Verification Scripts")
    print("="*40 + "\n")
    
    all_passed = True
    
    for script in scripts:
        print(f"▶️ Testing: {script} ... ", end="", flush=True)
        try:
            # Run script and capture output
            # We assume scripts run from project root, so we adjust path
            script_path = Path(__file__).parent / script
            completed = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent # Run from project root
            )
            
            if completed.returncode == 0:
                print("[+] PASS")
            else:
                print("[-] FAIL")
                print(f"\n--- Output of {script} ---")
                print(completed.stdout)
                print(completed.stderr)
                print("-" * 30 + "\n")
                all_passed = False
        except Exception as e:
            print(f"[-] CRASH: {e}")
            all_passed = False
            
    if all_passed:
        print("\n[*] ALL SYSTEMS GO: Zero Errors Detected. [*]")
    else:
        print("\n[!] SOME VERIFICATION STEPS FAILED.")
            
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
