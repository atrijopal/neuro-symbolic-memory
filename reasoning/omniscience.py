# reasoning/omniscience.py
import requests
import json
from config import OLLAMA_BASE_URL, EXTRACTION_MODEL

def detect_contradiction(new_fact: dict, existing_fact: dict) -> bool:
    """
    Uses LLM to determine if two facts are contradictory.
    Returns True if they logically conflict.
    """
    
    # Format facts as sentences
    new_stmt = f"{new_fact['src']} {new_fact['relation']} {new_fact['dst']}"
    old_stmt = f"{existing_fact['src']} {existing_fact['relation']} {existing_fact['dst']}"
    
    prompt = f"""
    Analyze these two statements for logical contradiction.
    
    Statement A (Old Knowledge): "{old_stmt}"
    Statement B (New Input): "{new_stmt}"
    
    Do these statements contradict each other? 
    - "I like apples" vs "I hate apples" -> YES
    - "I live in NY" vs "I live in SF" -> YES (assuming current residence)
    - "I ate pizza" vs "I ate sushi" -> NO (can eat both at different times)
    - "My name is Bob" vs "My name is Robert" -> NO (synonyms)
    
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
        print(f"[Omniscience] Raw Response: {result['response']}")
        data = json.loads(result['response'])
        return data.get("contradiction", False)
        
    except Exception as e:
        print(f"[Omniscience] Error checking contradiction: {e}")
        import traceback
        traceback.print_exc()
        return False
