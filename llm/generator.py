# llm/generator.py

import requests
from typing import List, Dict
from config import OLLAMA_BASE_URL, GENERATION_MODEL, GENERATION_TEMPERATURE

# Fallback when LLM is unavailable
DEFAULT_FALLBACK = "I'm here. Could you rephrase or tell me a bit more?"

QUESTION_WORDS = (
    "what", "when", "where", "who", "why", "how", "do i", "did i", "am i"
)


def _is_question(text: str) -> bool:
    t = text.lower().strip()
    return (
        t.endswith("?")
        or any(t.startswith(w) for w in QUESTION_WORDS)
    )


def generate_response(
    user_input: str,
    recent_turns: List[str],
    memories: List[Dict],
    session_id: str = None,
) -> str:
    """
    Generate assistant response.
    Never says 'I don't know' bluntly. Returns a safe fallback on LLM errors.
    """
    from datetime import datetime
    
    is_question = _is_question(user_input)
    has_memory = bool(memories)
    current_year = datetime.now().year

    # -------------------------
    # SYSTEM PROMPT (STRICT) - Updated to prevent old data confusion
    # -------------------------
    system_prompt = f"""You are a helpful and friendly assistant. Your goal is to have a natural, flowing conversation. Today is {datetime.now().strftime('%B %d, %Y')}.

RULES:
- When answering questions, use the "Relevant facts" provided below.
- If no relevant facts are available, answer the question based on general knowledge or ask for clarification.
- When the user provides new information, acknowledge it naturally (e.g., "Okay, I'll remember that.").
- Seamlessly integrate facts into your response. Do NOT say "according to my facts" or "based on my memory".
- Keep your responses concise and conversational."""

    # -------------------------
    # CONVERSATION HISTORY (SHORT-TERM CONTEXT)
    # -------------------------
    conversation_history = ""
    if recent_turns:
        conversation_history = "\nRecent conversation:\n"
        for turn in recent_turns[-3:]:  # Last 3 turns for context
            conversation_history += f"- {turn}\n"

    # -------------------------
    # MEMORY BLOCK (ONLY IF NEEDED) - Filtered and contextualized
    # -------------------------
    memory_block = ""
    if has_memory:
        memory_block = "Relevant facts (use ONLY these):\n"
        for m in memories:
            if isinstance(m, str):
                # Pre-formatted string (e.g. from ContextCompressor)
                memory_block += f"{m}\n"
            elif "content" in m:
                # Vector memory (unstructured) - use as-is but mark as fact
                content = str(m.get('content', '')).strip()
                if content:
                    memory_block += f"- {content}\n"
            else:
                # Symbolic memory (structured) - format clearly
                src = m.get('src', 'User')
                relation = m.get('relation', '')
                dst = m.get('dst', '')
                if src and relation and dst:
                    memory_block += f"- {src} {relation} {dst}\n"
        
        memory_block += "\nRemember: Only use facts listed above. Do not invent or assume anything else. This is the most important task. You cannot invent new stuff."

    # -------------------------
    # MODE SELECTION
    # -------------------------
    if not is_question:
        # User is stating something
        user_message = (
            f"{conversation_history}"
            f"{memory_block}\n"
            f"User statement: {user_input}\n"
            "Respond naturally and briefly."
        )

    elif is_question and has_memory:
        # Question + memory
        user_message = (
            f"{conversation_history}"
            f"{memory_block}\n"
            f"User question: {user_input}\n"
            "Answer using the known facts only."
        )

    else:
        # Question but no memory
        user_message = (
            f"{conversation_history}"
            f"User question: {user_input}\n"
            "Respond with a relevant general answer or ask one short clarification."
        )

    # -------------------------
    # CALL OLLAMA
    # -------------------------
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/v1/chat/completions",
            json={
                "model": GENERATION_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": GENERATION_TEMPERATURE,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
        if content:
            return content.strip()
    except (requests.RequestException, KeyError, IndexError, TypeError):
        pass
    return DEFAULT_FALLBACK
