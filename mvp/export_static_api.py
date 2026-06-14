import os
import sys
import json
import sqlite3
import time

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))
from memory_engine import get_connection

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def export_api():
    print("Exporting static API JSON from SQLite database...")
    
    public_api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public", "api"))
    ensure_dir(public_api_dir)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Helper to derive type
    def get_type(b_id, subject):
        if b_id.startswith("ep_"): return "EPISODIC"
        if b_id.startswith("dec_") or subject.upper() == "DECISION": return "DECISION"
        return "SEMANTIC"
    
    # 1. Export Memory (Nodes & Edges)
    cursor.execute("SELECT id, subject, predicate, object, payload, confidence, timestamp, status, author_id FROM beliefs WHERE status != 'FORGOTTEN'")
    beliefs = []
    
    semantic_count = 0
    episodic_count = 0
    decision_count = 0
    
    for row in cursor.fetchall():
        b_id = row[0]
        subj = row[1]
        payload = row[4]
        
        b_type = get_type(b_id, subj)
        if b_type == "EPISODIC": episodic_count += 1
        elif b_type == "DECISION": decision_count += 1
        else: semantic_count += 1
        
        # content logic for frontend
        content = payload if payload else f"{subj} {row[2]} {row[3]}"
        
        beliefs.append({
            "id": b_id,
            "content": content,
            "confidence": row[5],
            "type": b_type,
            "status": row[7],
            "created_at": row[6],
            "access_count": 0
        })
        
    edges = []
    # In edges table: source_id, target_id, relation_type. NO weight or timestamp!
    cursor.execute("SELECT source_id, target_id, relation_type FROM edges")
    for row in cursor.fetchall():
        edges.append({
            "source": row[0],
            "target": row[1],
            "relation_type": row[2],
            "weight": 1.0,
            "created_at": time.time()
        })
        
    with open(os.path.join(public_api_dir, "memory.json"), "w", encoding="utf-8") as f:
        json.dump({"nodes": beliefs, "edges": edges}, f, indent=2)
        
    # 2. Export Decisions
    decisions = []
    cursor.execute("SELECT id, subject, predicate, object, payload, timestamp FROM beliefs")
    for row in cursor.fetchall():
        b_id = row[0]
        subj = row[1]
        if get_type(b_id, subj) == "DECISION":
            decisions.append({
                "id": b_id,
                "content": row[4] if row[4] else f"{subj} {row[2]} {row[3]}",
                "timestamp": row[5]
            })
            
    decisions.sort(key=lambda x: x["timestamp"], reverse=True)
        
    with open(os.path.join(public_api_dir, "decisions.json"), "w", encoding="utf-8") as f:
        json.dump(decisions, f, indent=2)
        
    # 3. Export Metrics
    edge_count = len(edges)
    
    compression_ratio = 0.0
    total_active = episodic_count + semantic_count
    if total_active > 0:
        compression_ratio = semantic_count / total_active
        
    metrics = {
        "semantic_count": semantic_count,
        "episodic_count": episodic_count,
        "decision_count": decision_count,
        "audit_count": edge_count,
        "compression_ratio": round(compression_ratio, 2)
    }
    
    with open(os.path.join(public_api_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    conn.close()
    print("Export complete.")

if __name__ == "__main__":
    export_api()
