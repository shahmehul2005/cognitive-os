import time
import json
from consolidation_daemon import ConsolidationEngine, MemoryNode

def run_sleep_test():
    print("=========================================================")
    print("COGNITIVE OS: SLEEP PHASE TEST (CONSOLIDATION)")
    print("=========================================================")
    
    engine = ConsolidationEngine()
    current_time = time.time()
    
    # 1. Setup Active Memory with episodic logs
    
    # A noisy, old slack message with no inbound links (should be forgotten)
    node_noise = MemoryNode(
        id="ep_lunch_slack",
        type="Episodic",
        content="Did anyone order lunch?",
        last_retrieved=current_time - (30 * 86400), # 30 days old
        inbound_links=0
    )
    
    # The Valkey debate logs
    node_alice = MemoryNode(
        id="ep_alice_slack",
        type="Episodic",
        content="We need to switch from Redis to Valkey. Redis licensing changes are too risky.",
        last_retrieved=current_time - (1 * 86400), # 1 day old
        inbound_links=1
    )
    
    node_bob = MemoryNode(
        id="ep_bob_slack",
        type="Episodic",
        content="I disagree. A migration right now violates our Q3 Stability constraint.",
        last_retrieved=current_time - (1 * 86400), # 1 day old
        inbound_links=1
    )
    
    engine.add_episodic_memory(node_noise)
    engine.add_episodic_memory(node_alice)
    engine.add_episodic_memory(node_bob)
    
    print("\n--- STEP 1: INITIAL STATE ---")
    print(f"Active Memory Nodes: {len(engine.active_memory)}")
    print(f"Semantic/Decision Nodes: {len(engine.semantic_graph)}")
    
    print("\n--- STEP 2: TRIGGERING THE 2:00 AM SLEEP CYCLE ---")
    result = engine.sleep_cycle()
    
    print(f"\n[Sleep Complete] Decisions Abstracted: {result['decisions_abstracted']}")
    print(f"[Sleep Complete] Episodes Pruned (Forgotten): {result['episodes_pruned']}")
    
    print("\n--- STEP 3: FINAL STATE INSPECTION ---")
    print(f"Active Episodic Nodes remaining: {len(engine.active_memory)}")
    
    print("\n[Abstracted Semantic/Decision Graph]:")
    for node in engine.semantic_graph:
        print(f"  ID: {node.id}")
        print(f"  Type: {node.type}")
        print(f"  Payload: {json.dumps(node.payload, indent=2)}")
        
    print("\n[Cold Storage / Pruned Log]:")
    for node in engine.cold_storage:
        print(f"  ID: {node.id} (Pruned from Active Memory)")

    print("\n=========================================================")
    print("SLEEP PHASE TEST COMPLETE")
    print("=========================================================")

if __name__ == "__main__":
    run_sleep_test()
