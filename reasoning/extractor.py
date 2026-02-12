# reasoning/extractor.py

import json
import re
import requests
from typing import Optional, Dict, Any
from diagnostics.logger import log_event
from config import OLLAMA_BASE_URL, EXTRACTION_MODEL, EXTRACTION_TEMPERATURE, EXTRACTION_MAX_TOKENS


# Improved prompt with explicit location examples
SYSTEM_PROMPT = """
Return ONLY a JSON object describing a knowledge graph extracted from the user sentence.

Schema:
{
  "nodes": [{"id": "entity_name", "type": "category"}],
  "edges": [{"id": "e1", "src": "User", "dst": "entity_name", "relation": "RELATION_TYPE", "confidence": 1.0}]
}

Relation Types (use these specific types):
- ORIGIN_FROM: for "I am from X", "I'm from X", "from X" (where X is a place/location)
- LIVES_IN: for "I live in X"
- NAME_IS: for "my name is X", "I'm X", "I am X"
- MOTHER_NAME: for "my mom's name is X", "my mother is X"
- FATHER_NAME: for "my dad's name is X", "my father is X"
- LIKES: for "I like X", "I love X"
- DISLIKES: for "I hate X", "I dislike X"
- verb_phrase: ONLY for greetings, questions, or actions (NOT for personal facts)

Examples:
- "I am from Kerala" → {"edges": [{"id": "e1", "src": "User", "dst": "Kerala", "relation": "ORIGIN_FROM", "confidence": 1.0}]}
- "I'm from UP" → {"edges": [{"id": "e1", "src": "User", "dst": "UP", "relation": "ORIGIN_FROM", "confidence": 1.0}]}
- "my mom's name is Sita" → {"edges": [{"id": "e1", "src": "User", "dst": "Sita", "relation": "MOTHER_NAME", "confidence": 1.0}]}
- "hi" → {"nodes": [], "edges": []}

Rules:
- Extract personal facts, preferences, locations, and family facts.
- Use SPECIFIC relation types above (not generic "verb_phrase" for facts).
- Assign "confidence" (0.0 to 1.0): "I think" → 0.6, definite statements → 1.0.
- For greetings/questions with no personal fact, return {"nodes": [], "edges": []}.
- Do not output any text before or after the JSON object (no explanations, no code fences).
""".strip()


def _clean_json_string(s: str) -> str:
    """Aggressively clean string to extract JSON."""
    s = s.strip()
    # Remove markdown code blocks
    s = re.sub(r"```(?:json)?\s*", "", s)
    s = re.sub(r"```\s*$", "", s)
    s = s.strip()
    # Find first { and last }
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        s = s[start:end+1]
    return s.strip()


def _extract_json_from_content(content: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from LLM output with multiple fallback strategies."""
    if not content:
        return None
    
    content = content.strip()
    
    # Strategy 1: Try direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Clean and try again
    cleaned = _clean_json_string(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Extract JSON object from text
    match = re.search(r'\{[\s\S]*\}', content)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def extract_graph_delta(text: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """
    Extract knowledge graph delta from user input.
    Uses retry logic and multiple parsing strategies for reliability.
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()
    
    # Quick filter: skip obvious non-facts
    text_lower = text.lower()
    if text_lower in ("hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye"):
        return None
    
    for attempt in range(max_retries + 1):
        try:
            payload = {
                "model": EXTRACTION_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": EXTRACTION_TEMPERATURE,
                "max_tokens": EXTRACTION_MAX_TOKENS,
                # Ask the OpenAI-compatible endpoint to enforce JSON if supported.
                "response_format": {"type": "json_object"},
            }
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/v1/chat/completions",
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            
            data = response.json()
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
            
            if not content:
                if attempt < max_retries:
                    continue
                log_event("EXTRACTOR_FAIL", reason="empty_response", attempt=attempt+1)
                return None
            
            # Parse JSON with multiple strategies
            graph = _extract_json_from_content(content)
            
            if not graph or not isinstance(graph, dict):
                if attempt < max_retries:
                    log_event("EXTRACTOR_RETRY", reason="invalid_json", attempt=attempt+1, content_preview=content[:100])
                    continue
                log_event("EXTRACTOR_FAIL", reason="not_dict", content_preview=content[:100])
                return None
            
            # Validate structure
            if "edges" not in graph:
                graph["edges"] = []
            if "nodes" not in graph:
                graph["nodes"] = []
            
            # If no edges, return None (no facts extracted)
            if not graph["edges"]:
                return None
            
            # Validate and clean edges
            valid_edges = []
            for e in graph["edges"]:
                if not isinstance(e, dict):
                    continue
                if not all(k in e for k in ("id", "src", "dst", "relation")):
                    log_event("EXTRACTOR_WARN", reason="incomplete_edge", edge=str(e))
                    continue
                # Remove any extra fields
                clean_edge = {
                    "id": str(e["id"]),
                    "src": str(e["src"]),
                    "dst": str(e["dst"]),
                    "relation": str(e["relation"]),
                    "confidence": float(e.get("confidence", 1.0)),
                }
                valid_edges.append(clean_edge)
            
            if not valid_edges:
                log_event("EXTRACTOR_FAIL", reason="no_valid_edges")
                return None
            
            graph["edges"] = valid_edges
            
            # Validate and clean nodes
            valid_nodes = []
            for n in graph.get("nodes", []):
                if not isinstance(n, dict):
                    continue
                if "id" not in n:
                    continue
                clean_node = {
                    "id": str(n["id"]),
                    "type": str(n.get("type", "Entity")),
                }
                valid_nodes.append(clean_node)
            
            graph["nodes"] = valid_nodes
            
            return graph
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                log_event("EXTRACTOR_RETRY", reason="network_error", attempt=attempt+1, error=str(e))
                continue
            log_event("EXTRACTOR_FAIL", reason="network_error", error=str(e))
            return None
        except Exception as e:
            log_event("EXTRACTOR_FAIL", reason="unexpected_error", error=str(e))
            return None
    
    return None
