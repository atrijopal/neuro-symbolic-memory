# llm/verifier.py

import requests
from config import OLLAMA_BASE_URL, EXTRACTION_MODEL


def extract_memory_with_llm(text: str):
    """
    Uses Phi to extract a structured memory.
    Returns JSON string or None.
    """

    prompt = f"""You are a memory extraction engine for a personal AI assistant.

Extract a memory IF AND ONLY IF the statement contains:
- a stable personal preference
- a long-term constraint
- a personal fact
- a commitment or intent

Explicit first-person statements like "I like X", "I love X", "I don't do X", "I am allergic to X" MUST be extracted.

Do NOT extract: greetings, questions, general knowledge, opinions about the world.

If a memory exists, return STRICT JSON ONLY. If no memory exists, return null.

Schema: {{ "type": "...", "entity": "...", "attribute": "...", "value": "...", "explicit": true or false }}

Examples:
Input: "i like mango" -> {{"type":"preference","entity":"food","attribute":"liked","value":"mango","explicit":true}}
Input: "hello there" -> null

Rules: No explanations, no markdown, no extra text.

User statement: {text}"""

    response = requests.post(
        f"{OLLAMA_BASE_URL}/v1/chat/completions",
        json={
            "model": EXTRACTION_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
        },
        timeout=45,
    )

    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"].strip()

    if content.lower() == "null":
        return None

    return content

def verify_yes_no(prompt: str) -> bool:
    """
    Ask LLM a strict YES/NO question.
    Returns True for YES, False otherwise.
    """

    full_prompt = (
        "Answer ONLY with YES or NO.\n"
        f"{prompt}"
    )

    response = requests.post(
        f"{OLLAMA_BASE_URL}/v1/chat/completions",
        json={
            "model": EXTRACTION_MODEL,
            "messages": [
                {"role": "user", "content": full_prompt},
            ],
            "temperature": 0.0,
        },
        timeout=30,
    )

    response.raise_for_status()

    answer = response.json()["choices"][0]["message"]["content"].strip().upper()
    return answer.startswith("YES")
