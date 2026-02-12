# reasoning/omniscience.py
import requests
import json
from config import OLLAMA_BASE_URL, EXTRACTION_MODEL
from diagnostics.logger import log_event

def detect_contradiction(new_fact: dict, existing_fact: dict) -> bool:
    """
    Uses LLM to determine if two facts are contradictory.
    Returns True if they logically conflict.
    """
    
    # Format facts as sentences
    new_stmt = f"{new_fact['src']} {new_fact['relation']} {new_fact['dst']}"
    old_stmt = f"{existing_fact['src']} {existing_fact['relation']} {existing_fact['dst']}"
    
    prompt = f"""
    Analyze these two statements for logical contradiction. Only flag TRUE contradictions about IDENTITY, LOCATION, PREFERENCES, or RELATIONSHIPS.
    
    Statement A (Old Knowledge): "{old_stmt}"
    Statement B (New Input): "{new_stmt}"
    
    Rules:
    - If Statement B contains "unknown" or is a QUESTION, it is NOT a contradiction -> NO
    - Greetings/actions are NOT contradictions: "User greeted" vs "User asked" -> NO  
    - Different verb phrases are NOT contradictions unless they express opposite states
    - Identity conflicts ARE contradictions: "My name is Bob" vs "My name is Alice" -> YES
    - Location conflicts ARE contradictions: "I am from NY" vs "I am from SF" -> YES
    - Preference conflicts ARE contradictions: "I like apples" vs "I hate apples" -> YES
    - Synonyms/similar things are NOT contradictions: "Bob" vs "Robert" -> NO
    - Past actions are NOT contradictions: "I ate pizza" vs "I ate sushi" -> NO
    - Questions about existing facts are NOT contradictions -> NO
    
    Reply ONLY with JSON: {{"contradiction": true}} or {{"contradiction": false}}.
    """
    
    try:
        # Uses smaller model for speed
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": EXTRACTION_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        # Removed verbose OMNISCIENCE_RAW logging
        data = json.loads(result['response'])
        return data.get("contradiction", False)
        
    except Exception as e:
        log_event("OMNISCIENCE_ERROR", error=str(e))
        return False
