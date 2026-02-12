# tests/benchmark_latency.py
import time
import sys
from pathlib import Path
import statistics

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fast_pipe import fast_pipe
from slow_pipe import slow_pipe
from memory.neo4j_store import Neo4jMemoryStore

def benchmark():
    print("[FAST] Starting Latency Benchmark...")
    print("--------------------------------------------------")
    
    session_id = "benchmark_user"
    sample_query = "What did I say about my favorite food last week?"
    sample_statement = "I really love spicy ramen with extra egg."
    
    # 1. Warmup (to load models)
    print("Heating up the engines (Warmup)...")
    # Mock RAM context
    ram_context = {session_id: ["Previous turn context"]}
    
    try:
        fast_pipe(sample_query, session_id, ram_context)
    except Exception as e:
        print(f"Warmup warning: {e}")
        pass

    # 2. Benchmark Fast Pipe (Retrieval + Generation)
    print("\n[Fast Pipe] Measuring Retrieval & Generation Latency...")
    latencies = []
    for i in range(3):
        start = time.perf_counter()
        fast_pipe(sample_query, session_id, ram_context)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
        print(f"  Run {i+1}: {latencies[-1]:.2f} ms")
    
    avg_fast = statistics.mean(latencies)
    print(f"  👉 Average Fast Pipe: {avg_fast:.2f} ms")
    
    # 3. Benchmark Slow Pipe (Extraction + Storage)
    print("\n[Slow Pipe] Measuring Extraction & Storage Latency...")
    latencies = []
    for i in range(3):
        start = time.perf_counter()
        slow_pipe(sample_statement, session_id, ram_context)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
        print(f"  Run {i+1}: {latencies[-1]:.2f} ms")
        
    avg_slow = statistics.mean(latencies)
    print(f"  👉 Average Slow Pipe: {avg_slow:.2f} ms")
    
    # 4. Total System Latency Report
    print("\n--------------------------------------------------")
    print("📊 FINAL SCORECARD")
    print("--------------------------------------------------")
    print(f"Input Processing (Slow Pipe):   {avg_slow:.2f} ms")
    print(f"Response Time (Fast Pipe):      {avg_fast:.2f} ms")
    print("--------------------------------------------------")
    
    if avg_fast < 2000:
        print("[+] Status: REAL-TIME CAPABLE (< 2000ms)")
    elif avg_fast < 5000:
        print("[!] Status: ACCEPTABLE LAG (< 5000ms)")
    else:
        print("[-] Status: TOO SLOW (> 5000ms)")

if __name__ == "__main__":
    benchmark()
