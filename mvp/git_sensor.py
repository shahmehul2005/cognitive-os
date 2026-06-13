import sys
import os
import time
import subprocess
from typing import List

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from attention_engine import PerceivedEvent

def run_git_command(args: List[str]) -> str:
    try:
        res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def extract_structural_verbs(message: str) -> List[str]:
    """
    Fast, local NLP extraction to pull high/low entropy verbs from a commit message.
    Avoids LLM latency for the Perception loop.
    """
    msg_lower = message.lower()
    found_verbs = []
    
    high_entropy = ["migrate", "deprecate", "launch", "fail", "switch", "refactor", "architect"]
    low_entropy = ["fix", "update", "merge", "ping", "docs", "test", "minor"]
    
    for verb in high_entropy + low_entropy:
        if verb in msg_lower:
            found_verbs.append(verb)
            
    return found_verbs

def extract_entities(message: str) -> List[str]:
    """
    Simple keyword extraction for tracking infrastructure/strategy entities.
    """
    msg_lower = message.lower()
    found_entities = []
    
    key_entities = ["redis", "valkey", "sqlite", "gemini", "ui", "database", "api", "tms"]
    for entity in key_entities:
        if entity in msg_lower:
            found_entities.append(entity)
            
    return found_entities

class GitSensor:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        
    def fetch_recent_commits(self, limit: int = 10) -> List[PerceivedEvent]:
        """
        Connects to the live local Git repository and translates commits into PerceivedEvents.
        """
        git_logs = run_git_command(["git", "-C", self.repo_path, "log", f"-n", str(limit), "--pretty=format:%H|%an|%at|%s"])
        
        events = []
        if not git_logs:
            print("[GitSensor] Warning: No git logs found or not a git repository.")
            return events
            
        for line in git_logs.split("\n"):
            if "|" in line:
                h, author, timestamp_str, subject = line.split("|", 3)
                try:
                    ts = float(timestamp_str)
                except ValueError:
                    ts = time.time()
                    
                structural_verbs = extract_structural_verbs(subject)
                entities = extract_entities(subject)
                
                event = PerceivedEvent(
                    id=f"evt_git_{h[:8]}",
                    source="git",
                    payload=f"Commit by {author}: {subject}",
                    timestamp=ts,
                    entities=entities,
                    structural_verbs=structural_verbs
                )
                events.append(event)
                
        return events
