import sqlite3
import json
import uuid
import time
import math
import os
import gemini_client

DB_FILE = os.path.join(os.path.dirname(__file__), "memory_db.sqlite")

def get_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Episodic memory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodic (
        memory_id TEXT PRIMARY KEY,
        content TEXT,
        confidence REAL,
        provenance TEXT,
        importance_weight REAL,
        created_at REAL,
        last_retrieved REAL,
        access_count INTEGER,
        consolidated INTEGER DEFAULT 0
    )
    """)
    
    # Semantic memory table (ontology triples)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semantic (
        memory_id TEXT PRIMARY KEY,
        subject TEXT,
        predicate TEXT,
        object TEXT,
        confidence REAL,
        provenance TEXT,
        importance_weight REAL,
        created_at REAL,
        last_retrieved REAL,
        access_count INTEGER
    )
    """)
    
    # Decision memory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decision (
        decision_id TEXT PRIMARY KEY,
        content TEXT,
        timestamp REAL
    )
    """)
    
    # Failures memory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS failures (
        failure_id TEXT PRIMARY KEY,
        task_id TEXT,
        action_type TEXT,
        state_context TEXT,
        impact_severity REAL
    )
    """)
    
    # Audit log (cold storage)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id TEXT PRIMARY KEY,
        memory_id TEXT,
        type TEXT,
        raw_payload TEXT,
        archived_at REAL
    )
    """)
    
    # Vector Embeddings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        memory_id TEXT PRIMARY KEY,
        vector TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def cosine_similarity(v1, v2):
    dot_product = sum(x * y for x, y in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(x * x for x in v1))
    magnitude_v2 = math.sqrt(sum(x * x for x in v2))
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0.0
    return dot_product / (magnitude_v1 * magnitude_v2)

# Simulated active sub-graph cache
class ActiveCache:
    _cache = {} # memory_id -> node_dict
    
    @classmethod
    def add_node_and_neighbors(cls, node, vector):
        node_copy = dict(node)
        node_copy["vector"] = vector
        cls._cache[node["memory_id"]] = node_copy
        
    @classmethod
    def search(cls, query_vector, filters, limit=5):
        matches = []
        
        for node_id, node in cls._cache.items():
            # Check filters
            match_filter = True
            for k, v in filters.items():
                if node.get(k) != v:
                    match_filter = False
                    break
            if not match_filter:
                continue
                
            node_vector = node.get("vector")
            if node_vector:
                similarity = cosine_similarity(query_vector, node_vector)
                if similarity > 0.15: # threshold
                    node["cosine_similarity"] = similarity
                    matches.append(node)
                
        matches.sort(key=lambda x: x.get("cosine_similarity", 0), reverse=True)
        return matches[:limit]

def GetDecayRateForType(mem_type):
    if mem_type == "Episodic":
        return 0.1
    return 0.001

def RankImportance(node):
    dt = time.time() - node["last_retrieved"]
    decay_rate = GetDecayRateForType(node["type"])
    
    # Recency decay component
    recency_factor = math.exp(-decay_rate * dt)
    
    # Usage frequency component
    frequency_factor = math.log(node["access_count"] + 1) / (math.log(100) + 1)
    
    # Balanced score
    score = 0.5 * (node["importance_weight"] * recency_factor) + 0.5 * min(1.0, frequency_factor)
    return score

def Remember(content, memory_type, confidence_score, provenance_id):
    node_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()
    
    initial_importance = 0.8
    now = time.time()
    
    if memory_type == "Episodic":
        cursor.execute("""
        INSERT INTO episodic (memory_id, content, confidence, provenance, importance_weight, created_at, last_retrieved, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (node_id, json.dumps(content), confidence_score, provenance_id, initial_importance, now, now))
    elif memory_type == "Semantic":
        cursor.execute("""
        INSERT INTO semantic (memory_id, subject, predicate, object, confidence, provenance, importance_weight, created_at, last_retrieved, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (node_id, content.get("subject"), content.get("predicate"), content.get("object"), confidence_score, provenance_id, initial_importance, now, now))
        
    # Generate and store embedding vector
    vector = gemini_client.get_embedding(str(content))
    cursor.execute("INSERT INTO embeddings (memory_id, vector) VALUES (?, ?)", (node_id, json.dumps(vector)))
    
    conn.commit()
    conn.close()
    return node_id

def Retrieve(query_text, filters, k=5, min_activation_energy=0.1):
    # Fetch query embedding vector
    query_vector = gemini_client.get_embedding(query_text)
    
    # 1. Check local active sub-graph cache
    subgraph_candidates = ActiveCache.search(query_vector, filters, limit=k)
    results = []
    
    for node in subgraph_candidates:
        dynamic_energy = RankImportance(node)
        if dynamic_energy >= min_activation_energy:
            results.append((node, dynamic_energy))
            
    if len(results) >= k:
        return results[:k]
        
    # 2. Fallback: Search SQLite DB
    conn = get_connection()
    cursor = conn.cursor()
    
    mem_type = filters.get("type", "Episodic")
    candidates = []
    
    if mem_type == "Episodic":
        cursor.execute("SELECT memory_id, content, confidence, provenance, importance_weight, created_at, last_retrieved, access_count FROM episodic")
        for row in cursor.fetchall():
            candidates.append({
                "memory_id": row[0],
                "type": "Episodic",
                "content": json.loads(row[1]),
                "confidence": row[2],
                "provenance": row[3],
                "importance_weight": row[4],
                "created_at": row[5],
                "last_retrieved": row[6],
                "access_count": row[7]
            })
    elif mem_type == "Semantic":
        cursor.execute("SELECT memory_id, subject, predicate, object, confidence, provenance, importance_weight, created_at, last_retrieved, access_count FROM semantic")
        for row in cursor.fetchall():
            candidates.append({
                "memory_id": row[0],
                "type": "Semantic",
                "content": {"subject": row[1], "predicate": row[2], "object": row[3]},
                "confidence": row[4],
                "provenance": row[5],
                "importance_weight": row[6],
                "created_at": row[7],
                "last_retrieved": row[8],
                "access_count": row[9]
            })
            
    conn.close()
    
    matched_candidates = []
    
    # Load candidates vectors and compute similarity
    conn = get_connection()
    cursor = conn.cursor()
    
    for node in candidates:
        if node["memory_id"] in [r[0]["memory_id"] for r in results]:
            continue
            
        cursor.execute("SELECT vector FROM embeddings WHERE memory_id = ?", (node["memory_id"],))
        v_row = cursor.fetchone()
        if v_row:
            node_vector = json.loads(v_row[0])
            similarity = cosine_similarity(query_vector, node_vector)
            
            # If similarity is above semantic threshold
            if similarity > 0.15:
                node["cosine_similarity"] = similarity
                node["vector"] = node_vector
                matched_candidates.append(node)
                
    # Compute dynamic decay and update statistics
    for node in matched_candidates:
        dynamic_energy = RankImportance(node)
        if dynamic_energy >= min_activation_energy:
            node["access_count"] += 1
            node["last_retrieved"] = time.time()
            
            if mem_type == "Episodic":
                cursor.execute("UPDATE episodic SET access_count = ?, last_retrieved = ? WHERE memory_id = ?",
                               (node["access_count"], node["last_retrieved"], node["memory_id"]))
            elif mem_type == "Semantic":
                cursor.execute("UPDATE semantic SET access_count = ?, last_retrieved = ? WHERE memory_id = ?",
                               (node["access_count"], node["last_retrieved"], node["memory_id"]))
                               
            ActiveCache.add_node_and_neighbors(node, node["vector"])
            results.append((node, dynamic_energy))
            
    conn.commit()
    conn.close()
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:k]
