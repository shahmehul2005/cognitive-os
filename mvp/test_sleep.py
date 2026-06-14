import time
import json
from consolidation_daemon import ConsolidationDaemon
from memory_engine import BeliefStore

def run_sleep_test():
    print("=========================================================")
    print("COGNITIVE OS: SLEEP PHASE TEST (CONSOLIDATION)")
    print("=========================================================")
    
    BeliefStore.init_db()
    current_time = time.time()
    
    # 1. Setup Active Memory with episodic beliefs directly in the DB
    
    # A noisy, old slack message (should be forgotten)
    BeliefStore.insert_belief(
        belief_id="ep_lunch_slack",
        subject="lunch",
        predicate="order",
        object_val="pizza",
        payload="Did anyone order lunch?",
        confidence=0.8,
        decay_rate=0.07,  # Episodic fast decay
        timestamp=current_time - (30 * 86400), # 30 days old
        status="ACTIVE",
        author_id="junior_dev"
    )
    
    # A strategic debate log (should be retained because it's recent and structural)
    BeliefStore.insert_belief(
        belief_id="ep_alice_slack",
        subject="system architecture",
        predicate="migrate_to",
        object_val="valkey",
        payload="We need to switch from Redis to Valkey. Redis licensing changes are too risky.",
        confidence=0.9,
        decay_rate=0.01,  # Structural slow decay
        timestamp=current_time - (2 * 86400), # 2 days old
        status="ACTIVE",
        author_id="alice_founder"
    )
    
    daemon = ConsolidationDaemon()
    
    active_before = BeliefStore.get_all_active_beliefs()
    print("\n--- STEP 1: INITIAL STATE ---")
    print(f"Active Beliefs in DB: {len(active_before)}")
    for b in active_before:
        print(f"  - {b['subject']} {b['predicate']} {b['object']} (Conf: {b['confidence']})")
    
    print("\n--- STEP 2: TRIGGERING THE 2:00 AM SLEEP CYCLE ---")
    daemon.run_sleep_cycle()
    
    print("\n--- STEP 3: FINAL STATE INSPECTION ---")
    active_after = BeliefStore.get_all_active_beliefs()
    print(f"Active Beliefs remaining: {len(active_after)}")
    for b in active_after:
        print(f"  - {b['subject']} {b['predicate']} {b['object']} (Status: {b['status']})")
        
    print("\n=========================================================")
    print("SLEEP PHASE TEST COMPLETE")
    print("=========================================================")

if __name__ == "__main__":
    run_sleep_test()
