import os
import sys
import json
import time
import urllib.request
import urllib.error

sys.path.append(os.path.dirname(__file__))
from memory_engine import BeliefStore
import gemini_client

class GitHubGoalSensor:
    def __init__(self, repo_name="shahmehul2005/cognitive-os"):
        self.repo_name = repo_name
        self.token = os.environ.get("GITHUB_TOKEN", "")
        
    def fetch_open_goals(self):
        url = f"https://api.github.com/repos/{self.repo_name}/issues?state=open&labels=goal"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Cognitive-OS-Goal-Sensor"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
            
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                issues = json.loads(response.read().decode("utf-8"))
                return issues
        except urllib.error.HTTPError as e:
            print(f"[Goal Sensor] HTTP Error fetching issues: {e.code}")
            return []
        except Exception as e:
            print(f"[Goal Sensor] Error fetching issues: {e}")
            return []

    def process_goals(self):
        print(f"[Goal Sensor] Fetching active goals from {self.repo_name}...")
        issues = self.fetch_open_goals()
        
        if not issues:
            print("[Goal Sensor] No active goals found.")
            return
            
        for issue in issues:
            issue_id = f"goal_issue_{issue['number']}"
            title = issue.get("title", "")
            body = issue.get("body", "") or ""
            
            # Use Gemini to extract the core strategic intent if possible
            intent = title
            if gemini_client.has_api_key() and body:
                prompt = f"Extract the core technical or business intent from this GitHub Issue in one short sentence.\nTitle: {title}\nBody: {body}"
                extracted = gemini_client.generate_content(prompt)
                if extracted:
                    intent = extracted.strip()
            
            print(f"  -> Extracted Goal: {intent}")
            
            payload = {
                "title": title,
                "url": issue.get("html_url", ""),
                "intent": intent
            }
            
            # Insert into TMS
            BeliefStore.insert_belief(
                belief_id=issue_id,
                subject="organization",
                predicate="has_goal",
                object_val=intent[:50], # Abbreviated for graph edge
                payload=json.dumps(payload),
                confidence=0.99, # Goals have high confidence until closed
                decay_rate=0.01,
                timestamp=time.time(),
                status="ACTIVE",
                author_id=issue.get("user", {}).get("login", "unknown")
            )
        
        print(f"[Goal Sensor] Successfully processed {len(issues)} goals.")

if __name__ == "__main__":
    from memory_engine import setup_database
    setup_database()
    sensor = GitHubGoalSensor()
    sensor.process_goals()
