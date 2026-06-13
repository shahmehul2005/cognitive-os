import os
import json
import urllib.request
import urllib.error
import hashlib

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Load API key from local .env file if environment variable is not set
if not API_KEY:
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("GEMINI_API_KEY=", 1)[1].strip()
                        if val.startswith(('"', "'")) and val.endswith(('"', "'")):
                            val = val[1:-1]
                        API_KEY = val
                        break
    except Exception:
        pass

def has_api_key():
    return len(API_KEY) > 0

def call_gemini_api(url, payload):
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[Gemini Client Error] HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"[Gemini Client Error] Connection Error: {e}")
        return None

def generate_content(prompt, system_instruction=None, json_mode=False):
    if not has_api_key():
        # Mock responses when API key is missing
        return mock_generate_content(prompt, json_mode)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    
    contents = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    if system_instruction:
        contents["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    if json_mode:
        contents["generationConfig"] = {
            "responseMimeType": "application/json"
        }
        
    res = call_gemini_api(url, contents)
    if res and "candidates" in res and len(res["candidates"]) > 0:
        return res["candidates"][0]["content"]["parts"][0]["text"]
    return None

def get_embedding(text):
    if not has_api_key():
        # Mock embedding using hashing
        return mock_get_embedding(text)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={API_KEY}"
    
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {
            "parts": [{"text": text}]
        }
    }
    
    res = call_gemini_api(url, payload)
    if res and "embedding" in res:
        return res["embedding"]["values"]
    return mock_get_embedding(text)

def mock_generate_content(prompt, json_mode):
    # Very simple mock generator for consolidation fact extraction
    prompt_lower = prompt.lower()
    if json_mode and "fact_extraction" in prompt_lower or "subject" in prompt_lower:
        if "sqlite" in prompt_lower:
            return json.dumps([{"subject": "SQLite", "predicate": "usedFor", "object": "Database"}])
        return "[]"
    elif "summarise" in prompt_lower or "summary" in prompt_lower:
        return "Topics: Database initialization.\nDecisions: Selected SQLite.\nAction items: None."
    return "Mocked Gemini Response."

def mock_get_embedding(text):
    # Deterministic mock 768-dimension vector using sha256 hashing
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vector = []
    # Fill 768 dimensions using repeating hash bytes scaled to floats
    for i in range(768):
        byte_val = h[i % len(h)]
        val = (byte_val / 255.0) * 2.0 - 1.0 # normalize to [-1.0, 1.0]
        vector.append(val)
    return vector
