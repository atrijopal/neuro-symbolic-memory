# evaluation/retrieval_test.py

from memory.sqlite_store import SQLiteMemoryStore
from memory.chroma_store import ChromaMemoryStore
from reasoning.reranker import rerank_memories


def run_retrieval_test():
    print("=== RETRIEVAL TEST ===")

    store = SQLiteMemoryStore()
    chroma = ChromaMemoryStore()

    user_id = "retrieval_user"

    # Insert irrelevant symbolic memories
    for i in range(20):
        store.insert_memory({
            "memory_id": f"irrelevant_{i}",
            "user_id": user_id,
            "turn_id": i,
            "type": "fact",
            "entity": f"noise{i}",
            "attribute": "value",
            "value": f"junk{i}",
            "confidence": 0.3,
            "source_text": f"junk memory {i}",
        })

    # Insert relevant memory
    store.insert_memory({
        "memory_id": "relevant_1",
        "user_id": user_id,
        "turn_id": 100,
        "type": "constraint",
        "entity": "drink",
        "attribute": "restriction",
        "value": "no coffee",
        "confidence": 0.9,
        "source_text": "I don't drink coffee",
    })

    chroma.add(
        "I don't drink coffee",
        {"memory_id": "relevant_1", "entity": "drink"},
    )

    symbolic = store.retrieve_candidates(user_id, ["drink"])
    neural = chroma.query("coffee")

    top = rerank_memories(
        query="What do I drink?",
        symbolic_memories=symbolic,
        neural_memories=neural,
        top_k=3,
    )

    print("Top memories:")
    for m in top:
        print(m)

    if any("coffee" in str(m).lower() for m in top):
        print("RETRIEVAL TEST: PASS")
    else:
        print("RETRIEVAL TEST: FAIL")


if __name__ == "__main__":
    run_retrieval_test()
