import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from git_sensor import GitSensor
from attention_engine import AttentionEngine

def run_perception_test():
    print("=========================================================")
    print("COGNITIVE OS: LIVE PERCEPTION TEST (GIT SENSOR)")
    print("=========================================================")
    
    # Target the root directory of the repository
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    sensor = GitSensor(repo_path=repo_path)
    attention = AttentionEngine()
    
    print(f"\n[GitSensor] Fetching last 5 commits from: {repo_path}")
    events = sensor.fetch_recent_commits(limit=5)
    
    if not events:
        print("No commits found. Are you sure this is a Git repository?")
        return
        
    print("\n--- ATTENTION ENGINE ROUTING ---")
    
    for event in events:
        print(f"\nCommit: {event.payload}")
        print(f"  Extracted Entities: {event.entities}")
        print(f"  Structural Verbs: {event.structural_verbs}")
        
        score = attention.process(event)
        print(f"  Attention Score: {score.total_score:.2f} (Entropy Wgt: {score.entropy_val})")
        print(f"  Routing Actions: {score.routes}")
        
        if "ShouldReason" in score.routes:
            print("  >>> TRIGGER: Routing to Truth Maintenance System (TMS) for structural evaluation.")
        elif "ShouldRemember" in score.routes:
            print("  >>> TRIGGER: Routing to Semantic Memory.")
        else:
            print("  >>> TRIGGER: Ignoring / Routing to Episodic Cold Storage.")

    print("\n=========================================================")
    print("PERCEPTION TEST COMPLETE")
    print("=========================================================")

if __name__ == "__main__":
    run_perception_test()
