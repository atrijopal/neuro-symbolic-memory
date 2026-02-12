# reasoning/compressor.py

from typing import List, Dict

class ContextCompressor:
    def __init__(self, max_chars: int = 4000):
        self.max_chars = max_chars

    def compress(self, memories: List[Dict]) -> str:
        """
        Compresses a list of memory dictionaries into a single context string.
        - De-duplicates (fuzzy)
        - Formats nicely
        - Truncates if exceeding max_chars
        """
        unique_texts = set()
        formatted_lines = []
        
        current_chars = 0
        
        for mem in memories:
            # Extract text content
            if "relation" in mem:
                text = f"{mem.get('src')} {mem.get('relation')} {mem.get('dst')}"
            else:
                text = mem.get("content") or mem.get("text") or ""
            
            clean_text = " ".join(text.split()) # Remove extra whitespace
            
            if clean_text not in unique_texts:
                unique_texts.add(clean_text)
                
                # Check length
                if current_chars + len(clean_text) > self.max_chars:
                    break
                
                formatted_lines.append(f"- {clean_text}")
                current_chars += len(clean_text)
        
        if not formatted_lines:
            return ""
            
        return "\n".join(formatted_lines)
