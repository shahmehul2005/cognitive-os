import os
import sys

# Reconfigure stdout/stderr to UTF-8 for Windows terminal compatibility
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.append(os.path.dirname(__file__))

from git_sensor import GitSensor
from attention_engine import AttentionEngine
from memory_engine import setup_database
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
            from memory_engine import BeliefStore
            # Generate a unique subject/predicate for commits if not extracted
            import time
            BeliefStore.insert_belief(
                belief_id=f"ep_{event.id}",
                subject="git_commit",
                predicate="contains",
                object_val=event.id,
                payload=event.payload,
                confidence=0.8,
                decay_rate=0.07,
                timestamp=time.time(),
                status="ACTIVE",
                author_id=event.source
            )
            
    print("[Perception] Running Goal Ingestion (GitHub Issues)...")
    try:
        from github_goal_sensor import GitHubGoalSensor
        goal_sensor = GitHubGoalSensor()
        goal_sensor.process_goals()
    except Exception as e:
        print(f"Goal Sensor failed: {e}")
        
    print("[Perception] Running Communication Sensor (Slack)...")
    try:
        from slack_sensor import SlackSensor
        slack_sensor = SlackSensor()
        slack_sensor.process_slack()
    except Exception as e:
        print(f"Slack Sensor failed: {e}")
            
    print("[Consolidation] Triggering sleep cycle...")
    sleep_daemon.run_sleep_cycle()
    
if __name__ == "__main__":
    run_single_pass()
