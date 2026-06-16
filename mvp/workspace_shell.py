import sys
import os
import json
import time

# Reconfigure stdout/stderr to UTF-8 for Windows terminal compatibility
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from memory_engine import setup_database, get_connection
from decision_engine import Plan
from consolidation_daemon import Consolidate
from understanding_engine import Understand
import gemini_client

def print_banner():
    print("""
=========================================================
      ______                                 _    _             _ 
     |  ____|                               | |  (_)           | |
     | |__  __ _ _   _ _ __ ___  _ __   __ _| |_  _  ___  _ __ | |
     |  __|/ _` | | | | '_ ` _ \| '_ \ / _` | __|| |/ _ \| '_ \| |
     | |  | (_| | |_| | | | | | | |_) | (_| | |_ | | (_) | | | |_|
     |_|   \__,_|\__,_|_| |_| |_| .__/ \__,_|\__||_|\___/|_| |_(_)
                                | |                               
                                |_|                               
             Cognitive Operating System Shell v1.0
=========================================================
Type /help to list available commands.
Active Agent: Antigravity Co-Founder
""")
    if gemini_client.has_api_key():
        print("💡 [STATUS] Gemini API Key detected. Actual LLM & Vector search active.")
    else:
        print("⚠️ [STATUS] Gemini API Key NOT detected. Running in mock simulator mode.")

def print_help():
    print("""
Available Shell Commands:
  /chat <message>   - Log a conversation statement into episodic memory.
  /goals            - Load and display strategic target goals and constraints.
  /plan <goal_id>   - Traverse trajectories and audit plans to achieve a goal.
  /query <text>     - Search memory using vector cosine similarity.
  /sleep            - Trigger nightly offline memory consolidation and pruning.
  /help             - Show this help summary.
  /exit             - Exit the interactive shell.
""")

def print_goals():
    try:
        with open(os.path.join(os.path.dirname(__file__), "workspace_identity.json"), "r") as f:
            identity = json.load(f)
            
        print("\n=== SYSTEM IDENTITY & STRATEGY ===")
        print(f"🎯 Mission: {identity['mission']['core_purpose']}")
        print(f"🏁 Horizon: {identity['mission']['horizon']}")
        print(f"🗺️ Stage  : {identity['current_strategy']['stage']} (Focus: {identity['current_strategy']['focus']})")
        print("\n⭐ Core Values:")
        for val in identity["values"]:
            print(f"  - {val['name']}: {val['description']} (Weight: {val['weight']})")
            
        print("\n🛡️ Hard Constraints:")
        print(f"  - Monthly compute budget: ${identity['constraints']['resource_limits']['max_monthly_compute_budget_usd']:.2f}")
        print(f"  - Allow external script execution: {identity['constraints']['security']['allow_external_execution_without_approval']}")
        
        print("\n🎯 Active Goals:")
        for goal in identity["goals"]:
            print(f"  - [{goal['id']}] {goal['description']} (Status: {goal['status']})")
    except Exception as e:
        print(f"Error loading goals: {e}")

def run_shell():
    setup_database()
    print_banner()
    
    while True:
        try:
            user_input = input("\ncog-os> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting shell. Goodbye!")
            break
            
        if not user_input:
            continue
            
        if user_input.startswith("/exit"):
            print("Exiting shell. Goodbye!")
            break
        elif user_input.startswith("/help"):
            print_help()
        elif user_input.startswith("/goals"):
            print_goals()
        elif user_input.startswith("/chat "):
            msg = user_input[6:].strip()
            print("🧠 [Understanding] Analyzing message context...")
            model = Understand(msg)
            print("\n--- Situational Mental Model ---")
            print(f"🔹 Resolved Text: {model['resolved_text']}")
            print(f"🔹 Intent       : {model['intent']}")
            print(f"🔹 Sentiment    : {model['sentiment']}")
            if model['resolved_entities']:
                print("🔹 Resolved Entities:")
                for ent in model['resolved_entities']:
                    print(f"  - {ent['pronoun']} -> {ent['resolved_uri']} ({ent['type']})")
            print("--------------------------------\n")
            
            payload = {
                "text": msg,
                "resolved_text": model["resolved_text"],
                "intent": model["intent"],
                "sentiment": model["sentiment"],
                "resolved_entities": model["resolved_entities"]
            }
            from memory_engine import BeliefStore
            import time
            event_id = f"ep_{int(time.time())}"
            BeliefStore.insert_belief(
                belief_id=event_id,
                subject="chat_log",
                predicate="contains",
                object_val=model["intent"],
                payload=json.dumps(payload),
                confidence=0.95,
                decay_rate=0.07,
                timestamp=time.time(),
                status="ACTIVE",
                author_id="cli_session"
            )
            print(f"✔️ Conversation recorded to Episodic store (ID: {event_id})")
        elif user_input.startswith("/query "):
            query = user_input[7:].strip()
            print(f"🔎 Scanning semantic memory graphs for '{query}'...")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, payload, object FROM beliefs WHERE payload LIKE ? OR object LIKE ? LIMIT 5", (f"%{query}%", f"%{query}%"))
            retrieved = cursor.fetchall()
            conn.close()
            
            if not retrieved:
                print("❌ No matching memories found.")
            else:
                print(f"Found {len(retrieved)} matches:")
                for row in retrieved:
                    print(f"  - [{row[0][:8]}] Content: {row[1] or row[2]}")
        elif user_input.startswith("/plan "):
            goal_id = user_input[6:].strip()
            # Find goal in identity file
            try:
                with open(os.path.join(os.path.dirname(__file__), "workspace_identity.json"), "r") as f:
                    identity = json.load(f)
                goal = next((g for g in identity["goals"] if g["id"] == goal_id), None)
            except Exception:
                goal = None
                
            if not goal:
                print(f"❌ Goal ID '{goal_id}' not found. Check active goals using /goals.")
                continue
                
            print(f"🚀 Initializing simulator tree for target goal: '{goal['description']}'...")
            decision = Plan(goal)
            print("\n=== COMPARATIVE RECOMMENDATION MATRIX ===")
            print(f"Recommended Option: {decision['recommendation']}")
            print("\nOption Simulations:")
            for opt in decision["simulations"]:
                print(f"  * Option: {opt['option_id']}")
                print(f"    Steps: {', '.join(opt['steps'])}")
                print(f"    Risk Severity: {opt['risk_analysis']['severity']} (Score: {opt['risk_analysis']['severity_score']:.2f})")
                print(f"    Expected Success Probability: {opt['probability_of_success']:.2f}")
                print(f"    Computed Alignment Score: {opt['utility']:.2f}")
        elif user_input.startswith("/sleep"):
            print("💤 System entering consolidation sleep phase...")
            report = Consolidate()
            print("\n=== CONSOLIDATION REPORT ===")
            print(f"✏️ Abstracted Semantic Facts: {report['extracted_facts']}")
            print(f"🗑️ Pruned Decayed Episodic Indexes: {report['pruned_episodes']}")
            
            # Query audit log count
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(log_id) FROM audit_log")
            audit_count = cursor.fetchone()[0]
            conn.close()
            print(f"📦 Total archived logs in compliance store: {audit_count}")
        else:
            print("Command unrecognized. Type /help to see available commands.")

if __name__ == "__main__":
    run_shell()
