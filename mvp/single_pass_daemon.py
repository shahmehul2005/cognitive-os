import os
import sys

sys.path.append(os.path.dirname(__file__))

from git_sensor import GitSensor
from attention_engine import AttentionEngine
from memory_engine import Remember, setup_database
from consolidation_daemon import ConsolidationDaemon

def run_single_pass():
    setup_database()
    print("🚀 Running Cognitive OS Single Pass (GitHub Actions)")
    
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sensor = GitSensor(repo_path=repo_path)
    attention = AttentionEngine()
    sleep_daemon = ConsolidationDaemon()
    
    print("[Perception] Scanning for new events...")
    events = sensor.fetch_recent_commits(limit=5)
    
    for event in events:
        # For a single pass without state, we rely on the TMS to reject duplicates
        # based on identical subject/predicate. But for episodic it might insert duplicates.
        # We can just let it run. In a real scenario we'd query if the commit hash exists.
        print(f"  -> Processing: {event.payload}")
        score = attention.process(event)
        
        if "ShouldRemember" in score.routes or "ShouldReason" in score.routes:
            # We use the commit hash as part of the payload to prevent TMS duplicates if we wanted
            Remember(
                content={"text": event.payload, "verbs": event.structural_verbs, "entities": event.entities, "hash": event.id},
                type="EPISODIC",
                confidence=0.8,
                provenance=event.source
            )
            
    print("[Consolidation] Triggering sleep cycle...")
    sleep_daemon.run_sleep_cycle()
    
if __name__ == "__main__":
    run_single_pass()
