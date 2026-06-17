import os
import sys
import json
import time
import urllib.request
import urllib.error
import urllib.parse

sys.path.append(os.path.dirname(__file__))
from memory_engine import BeliefStore
import gemini_client

class SlackSensor:
    def __init__(self):
        self.token = os.environ.get("SLACK_BOT_TOKEN", "")
        self.channel_name = "architecture"
        
    def _call_api(self, endpoint, params=None):
        url = f"https://slack.com/api/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"[Slack Sensor] API Error ({endpoint}): {e}")
            return None

    def get_channel_id(self):
        # Fetch list of channels to find the #architecture channel
        res = self._call_api("conversations.list", {"types": "public_channel", "exclude_archived": "true"})
        if not res or not res.get("ok"):
            print("[Slack Sensor] Failed to fetch channels or token is invalid.")
            return None
            
        for channel in res.get("channels", []):
            if channel.get("name") == self.channel_name:
                return channel.get("id")
                
        print(f"[Slack Sensor] Channel #{self.channel_name} not found.")
        return None

    def fetch_recent_messages(self, channel_id, limit=20):
        # Calculate timestamp for 24 hours ago
        oldest = str(time.time() - 86400)
        res = self._call_api("conversations.history", {"channel": channel_id, "limit": limit, "oldest": oldest})
        if not res or not res.get("ok"):
            return []
        return res.get("messages", [])

    def process_slack(self):
        if not self.token:
            print("[Slack Sensor] SLACK_BOT_TOKEN not found. Skipping Slack ingestion.")
            return

        print(f"[Slack Sensor] Connecting to Slack workspace...")
        channel_id = self.get_channel_id()
        if not channel_id:
            return

        messages = self.fetch_recent_messages(channel_id)
        if not messages:
            print(f"[Slack Sensor] No new messages in #{self.channel_name} over the last 24h.")
            return
            
        # Filter out bot messages and empty texts
        user_messages = [m for m in messages if "bot_id" not in m and m.get("text")]
        
        if not user_messages:
            return
            
        # Combine messages to give Gemini context of the conversation
        conversation = "\n".join([f"User: {m['text']}" for m in reversed(user_messages)])
        print(f"[Slack Sensor] Analyzing {len(user_messages)} messages for architectural decisions...")
        
        if not gemini_client.has_api_key():
            print("[Slack Sensor] Gemini API key not found. Cannot extract intent.")
            return
            
        prompt = f"""
        Analyze the following Slack conversation from an #architecture channel.
        Did the team reach a consensus or make a structural engineering decision?
        If YES, extract the decision in a single sentence. If NO, reply exactly with "NO_DECISION".
        
        Conversation:
        {conversation}
        """
        
        extracted = gemini_client.generate_content(prompt)
        
        if not extracted or "NO_DECISION" in extracted.upper():
            print("[Slack Sensor] No clear architectural decision detected in recent messages.")
            return
            
        decision = extracted.strip()
        print(f"  -> Extracted Decision: {decision}")
        
        # Use the latest message's timestamp as the event ID
        latest_ts = user_messages[0].get("ts", str(time.time()))
        event_id = f"slack_dec_{latest_ts.replace('.', '')}"
        
        payload = {
            "source": "slack",
            "channel": self.channel_name,
            "decision": decision,
            "raw_context": conversation[:500] # store brief context
        }
        
        BeliefStore.insert_belief(
            belief_id=event_id,
            subject="architecture_team",
            predicate="decided",
            object_val=decision[:50],
            payload=json.dumps(payload),
            confidence=0.85, # High confidence for human explicit chat
            decay_rate=0.03,
            timestamp=float(latest_ts),
            status="ACTIVE",
            author_id="slack_team"
        )
        print("[Slack Sensor] Decision successfully logged to the Cognitive OS Graph.")

if __name__ == "__main__":
    from memory_engine import setup_database
    setup_database()
    sensor = SlackSensor()
    sensor.process_slack()
