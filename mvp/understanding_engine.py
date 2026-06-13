import os
import sys
import json
import time

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

import gemini_client
from memory_engine import get_connection

def get_recent_context(limit=5):
    """Retrieve recent episodic and semantic memory context to resolve coreferences."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch recent episodic entries
    cursor.execute("""
        SELECT content, created_at FROM episodic 
        ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    episodes = []
    for row in cursor.fetchall():
        try:
            episodes.append(json.loads(row[0]))
        except Exception:
            episodes.append(row[0])
            
    # Fetch recent semantic entries
    cursor.execute("""
        SELECT subject, predicate, object, created_at FROM semantic 
        ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    semantics = []
    for row in cursor.fetchall():
        semantics.append(f"{row[0]} {row[1]} {row[2]}")
        
    conn.close()
    return {
        "recent_episodes": episodes,
        "recent_facts": semantics
    }

def Understand(raw_text, local_context=None):
    """
    Translates raw attention signals (text) into resolved mental models.
    Resolves pronouns/coreferences, classifies intent and sentiment.
    """
    if not local_context:
        local_context = get_recent_context()
        
    prompt = f"""
    You are the Understanding module of a Cognitive OS.
    Your task is to analyze the input text and construct a Situational Mental Model by resolving coreferences, classifying intent, and identifying sentiment.
    
    Local Context (recent memories and facts):
    {json.dumps(local_context, indent=2)}
    
    Input Text:
    "{raw_text}"
    
    Please output a JSON object with the following fields:
    - "resolved_text": The input text with all ambiguous pronouns (like "it", "they", "this bug", "that release", "we") resolved to specific entities from the local context, or clearly described if not in context.
    - "resolved_entities": An array of objects, each representing a resolved pronoun. Fields: "pronoun", "resolved_uri" (if a file/doc is resolved, use file:/// prefix; otherwise provide a descriptive text name/id), "type" (e.g., "document", "technology", "actor", "action").
    - "intent": Categorize as one of: "Inquiry", "Instruction", "Objection", "Consensus", "Statement".
    - "sentiment": Describe sentiment (e.g., "neutral", "urgent", "optimistic", "skeptical", "objection").
    
    Return ONLY valid JSON.
    """
    
    fallback_model = {
        "resolved_text": raw_text,
        "resolved_entities": [],
        "intent": "Statement",
        "sentiment": "neutral"
    }
    
    res_text = gemini_client.generate_content(prompt, system_instruction="You are a precise Situational Model parser. Output JSON.", json_mode=True)
    if res_text:
        try:
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(res_text.strip())
            # Ensure required fields are present
            for field in ["resolved_text", "resolved_entities", "intent", "sentiment"]:
                if field not in data:
                    data[field] = fallback_model[field]
            return data
        except Exception:
            pass
            
    # Simple rule-based mock resolver if offline / failed
    text_lower = raw_text.lower()
    if "it" in text_lower or "this" in text_lower:
        sqlite_in_context = any("sqlite" in str(x).lower() for x in local_context.values())
        if sqlite_in_context:
            fallback_model["resolved_text"] = raw_text.replace("it", "SQLite").replace("this", "SQLite")
            fallback_model["resolved_entities"].append({
                "pronoun": "it" if "it" in text_lower else "this",
                "resolved_uri": "technology/sqlite",
                "type": "technology"
            })
            
    if "?" in raw_text:
        fallback_model["intent"] = "Inquiry"
    elif "should" in text_lower or "need to" in text_lower or "let's" in text_lower or "lets" in text_lower:
        fallback_model["intent"] = "Instruction"
        if "urgent" in text_lower or "asap" in text_lower or "must" in text_lower:
            fallback_model["sentiment"] = "urgent"
            
    return fallback_model
