# main.py

from memory.ram_context import RAMContext
from memory.reset import wipe_all_memory
from fast_pipe import fast_pipe

# Commands that wipe all memory (case-insensitive)
RESET_COMMANDS = {"reset", "wipe", "clear", "clear memory", "wipe memory", "delete memory", "forget all"}


def main():
    print("Neuro-Symbolic Memory Engine (V1)")
    print("--------------------------------")
    print("Commands: exit / quit = leave  |  reset / wipe / clear = delete ALL memory")
    print()

    session_id = "default_user"
    ram_context = RAMContext()

    while True:
        user_input = input("\nUser> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        # Delete all memory (DB + vector + RAM)
        if user_input.lower() in RESET_COMMANDS:
            try:
                wipe_all_memory(ram_context=ram_context)
                print("Assistant> All memory has been deleted. I've forgotten everything.")
            except Exception as e:
                print(f"Assistant> I encountered an error trying to wipe memory: {e}")
            continue

        ram_context.add(session_id, user_input)

        result = fast_pipe(
            user_input=user_input,
            session_id=session_id,
            ram_context=ram_context,
        )
        print(f"Assistant> {result['response']}")


if __name__ == "__main__":
    main()
