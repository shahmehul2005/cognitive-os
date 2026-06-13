import sys
import os
import time
import json
import sqlite3

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from memory_engine import setup_database, Remember, Retrieve, get_connection
from decision_engine import Plan
from consolidation_daemon import Consolidate

def run_test():
    print("=== COGNITIVE OS MVP: STARTING TEST SCENARIO ===")
    
    # Step 1: Initialize local SQLite database
    print("\n[Step 1] Initializing SQLite database tables...")
    setup_database()
    print("Database initialized successfully.")
    
    # Clear any previous run data
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM episodic")
    cursor.execute("DELETE FROM semantic")
    cursor.execute("DELETE FROM decision")
    cursor.execute("DELETE FROM failures")
    cursor.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()
    
    # Step 2: Simulate active decision path planning
    print("\n[Step 2] Executing Planning Engine for Database Selection Goal...")
    goal_state = {
        "goal_id": "goal_01",
        "description": "Initialize database engines and build collective memory schema."
    }
    decision_matrix = Plan(goal_state)
    print(f"Planning Recommendation: {decision_matrix['recommendation']}")
    print(f"Simulations Analyzed: {len(decision_matrix['simulations'])} options")
    
    # Step 3: Record an episodic event containing a decision statement
    print("\n[Step 3] Logging conversation episode to Episodic Memory...")
    episodic_content = {
        "text": "Founder A: Let's select SQLite as the database engine for MVP velocity."
    }
    event_id = Remember(content=episodic_content, memory_type="Episodic", confidence_score=0.95, provenance_id="slack_channel_1")
    print(f"Logged Event ID: {event_id}")
    
    # Step 4: Run Consolidation (Abstraction & Compression)
    print("\n[Step 4] Triggering sleep phase consolidation...")
    consolidation_report = Consolidate()
    print(f"Consolidation Report: {json.dumps(consolidation_report)}")
    
    # Step 5: Query memory retrieval
    print("\n[Step 5] Querying Memory Engine for 'What database engine are we using?'...")
    retrieved_nodes = Retrieve(query_text="What database engine are we using?", filters={"type": "Semantic"}, k=1, min_activation_energy=0.01)
    
    print(f"Retrieved Nodes count: {len(retrieved_nodes)}")
    for node, energy in retrieved_nodes:
        print(f"  - Node ID: {node['memory_id']}")
        print(f"  - Content: {node['content']}")
        print(f"  - Dynamic Activation Energy: {energy:.4f}")
        
    # Verify expected values
    assert len(retrieved_nodes) == 1, "Error: Semantic memory was not retrieved."
    retrieved_fact = retrieved_nodes[0][0]["content"]
    fact_str = str(retrieved_fact).lower()
    assert "sqlite" in fact_str, f"Error: Expected consolidated memory content to contain 'sqlite', got {retrieved_fact}"
    print("\n[SUCCESS] Memory retrieval correctly returned the consolidated fact.")
    
    # Step 6: Test memory decay, pruning, and compliance archiving
    print("\n[Step 6] Simulating temporal decay on episodic traces (accelerating time)...")
    
    # Manually shift timestamps of episodic traces backward by 30 days to force decay
    conn = get_connection()
    cursor = conn.cursor()
    thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
    cursor.execute("UPDATE episodic SET created_at = ?, last_retrieved = ? WHERE memory_id = ?",
                   (thirty_days_ago, thirty_days_ago, event_id))
    conn.commit()
    conn.close()
    
    print("Running consolidation sleep phase to prune decayed indexes...")
    consolidation_report = Consolidate()
    print(f"Consolidation Report: {json.dumps(consolidation_report)}")
    
    # Verify the episode was de-indexed but archived in audit log
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT memory_id FROM episodic WHERE memory_id = ?", (event_id,))
    active_episode = cursor.fetchone()
    
    cursor.execute("SELECT raw_payload FROM audit_log WHERE memory_id = ?", (event_id,))
    archived_log = cursor.fetchone()
    conn.close()
    
    assert active_episode is None, "Error: Decayed episode was not de-indexed from active database."
    assert archived_log is not None, "Error: Decayed episode was not saved to compliance audit log."
    
    print("\n[SUCCESS] Decayed index successfully de-indexed and archived to cold storage.")
    print("\n=== COGNITIVE OS MVP: ALL VERIFICATION SCENARIOS PASSED ===")

if __name__ == "__main__":
    run_test()
