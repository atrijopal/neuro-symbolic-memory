import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fast_pipe import fast_pipe
from memory.ram_context import RAMContext
from config import OLLAMA_BASE_URL
import requests

def check_ollama():
    try:
        requests.get(OLLAMA_BASE_URL)
        return True
    except:
        return False

def test_fast_pipe_performance():
    print("Testing Fast Pipe Performance...")
    
    if not check_ollama():
        print("[!] Ollama is not running. Performance test might fail or fallback.")
    
    user_input = "I am testing the system performance."
    session_id = "perf_test_user"
    ram_context = RAMContext()
    
    start = time.time()
    result = fast_pipe(user_input, session_id, ram_context)
    duration = time.time() - start
    
    print(f"Response: {result['response']}")
    print(f"Duration: {duration:.4f} seconds")
    
    if duration < 1.0:
        print("[+] Fast Pipe is FAST (< 1.0s)!")
    else:
        print("[!] Fast Pipe is slower than expected (check if using heavy model or if Ollama is slow).")
        
    # Check if slow pipe extraction was triggered (this is async, so we can't easily assert here without waiting/checking logs)
    print("Check logs for 'SLOW_PIPE_OK' to confirm background extraction.")
    time.sleep(3) # Allow background threads to complete before script exit

if __name__ == "__main__":
    test_fast_pipe_performance()
