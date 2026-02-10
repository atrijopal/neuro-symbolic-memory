# evaluation/contradiction_test.py

from memory.ram_context import RAMContext
from fast_pipe import fast_pipe
from memory.sqlite_store import SQLiteMemoryStore


def run_contradiction_test():
    print("=== CONTRADICTION TEST ===")

    session_id = "contradiction_user"
    ram_context = RAMContext()
    store = SQLiteMemoryStore()

    # Turn 1: constraint
    fast_pipe(
        user_input="I don't drink coffee",
        session_id=session_id,
        ram_context=ram_context,
    )

    # Turn 2: conflicting preference
    fast_pipe(
        user_input="I love coffee",
        session_id=session_id,
        ram_context=ram_context,
    )

    rows = store.retrieve_candidates(session_id, ["drink"])

    print("Memories retrieved:")
    for r in rows:
        print(r)

    constraint_count = sum(1 for r in rows if r["type"] == "constraint")
    preference_count = sum(1 for r in rows if r["type"] == "preference")

    if constraint_count == 1 and preference_count == 0:
        print("CONTRADICTION TEST: PASS")
    else:
        print("CONTRADICTION TEST: FAIL")


if __name__ == "__main__":
    run_contradiction_test()
