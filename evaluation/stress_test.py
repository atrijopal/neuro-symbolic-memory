# evaluation/stress_test.py

import time

from memory.ram_context import RAMContext
from fast_pipe import fast_pipe
from memory.sqlite_store import SQLiteMemoryStore


def run_stress_test(
    turns: int = 200,
    insert_every: int = 10,
):
    print("=== STRESS TEST ===")

    session_id = "stress_user"
    ram_context = RAMContext()
    store = SQLiteMemoryStore()

    latencies = []
    errors = 0

    for i in range(1, turns + 1):
        if i % insert_every == 0:
            user_input = f"I like item{i}"
        else:
            user_input = f"random filler {i}"

        start = time.time()
        try:
            fast_pipe(
                user_input=user_input,
                session_id=session_id,
                ram_context=ram_context,
            )
        except Exception:
            errors += 1

        latencies.append((time.time() - start) * 1000)

    rows = store.retrieve_candidates(session_id, ["item"])

    print(f"Turns executed      : {turns}")
    print(f"Errors              : {errors}")
    print(f"Avg latency (ms)     : {sum(latencies)/len(latencies):.2f}")
    print(f"Max latency (ms)     : {max(latencies):.2f}")
    print(f"Memories stored      : {len(rows)}")

    if errors == 0:
        print("STRESS TEST: PASS")
    else:
        print("STRESS TEST: FAIL")


if __name__ == "__main__":
    run_stress_test()
