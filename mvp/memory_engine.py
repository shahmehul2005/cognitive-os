import sqlite3
import json
import time
import os
import uuid
import math
import gemini_client

DB_FILE = os.path.join(os.path.dirname(__file__), "memory_db.sqlite")

def get_connection():
    # Enforce foreign keys and reliable writes
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Core Belief Graph Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beliefs (
        id TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        predicate TEXT NOT NULL,
        object TEXT,
        payload TEXT,
        confidence REAL NOT NULL,
        decay_rate REAL NOT NULL,
        timestamp REAL NOT NULL,
        status TEXT NOT NULL,
        author_id TEXT
    )
    """)
    
    # Graph Edges Table (e.g. for SUPERCEDED_BY, IMPLIES, CONTRADICTS)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        FOREIGN KEY(source_id) REFERENCES beliefs(id) ON DELETE CASCADE,
        FOREIGN KEY(target_id) REFERENCES beliefs(id) ON DELETE CASCADE,
        PRIMARY KEY (source_id, target_id, relation_type)
    )
    """)
    
    # Vector Embeddings table for semantic search
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        belief_id TEXT PRIMARY KEY,
        vector TEXT,
        FOREIGN KEY(belief_id) REFERENCES beliefs(id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

class BeliefStore:
    """The formal SQLite wrapper for the Belief Graph."""
    
    @staticmethod
    def init_db():
        setup_database()
        
    @staticmethod
    def insert_belief(belief_id, subject, predicate, object_val, payload, confidence, decay_rate, timestamp, status, author_id, vector=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO beliefs 
        (id, subject, predicate, object, payload, confidence, decay_rate, timestamp, status, author_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (belief_id, subject, predicate, object_val, payload, confidence, decay_rate, timestamp, status, author_id))
        
        if vector:
            cursor.execute("INSERT OR REPLACE INTO embeddings (belief_id, vector) VALUES (?, ?)", 
                           (belief_id, json.dumps(vector)))
            
        conn.commit()
        conn.close()

    @staticmethod
    def update_belief_status(belief_id, new_status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE beliefs SET status = ? WHERE id = ?", (new_status, belief_id))
        conn.commit()
        conn.close()
        
    @staticmethod
    def insert_edge(source_id, target_id, relation_type):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO edges (source_id, target_id, relation_type) VALUES (?, ?, ?)",
                       (source_id, target_id, relation_type))
        conn.commit()
        conn.close()
        
    @staticmethod
    def query_beliefs_by_key(subject, predicate):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, subject, predicate, object, payload, confidence, decay_rate, timestamp, status, author_id 
        FROM beliefs 
        WHERE subject = ? AND predicate = ?
        """, (subject, predicate))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "subject": row[1],
                "predicate": row[2],
                "object": row[3],
                "payload": row[4],
                "confidence": row[5],
                "decay_rate": row[6],
                "timestamp": row[7],
                "status": row[8],
                "author_id": row[9]
            })
        conn.close()
        return results

    @staticmethod
    def get_all_active_beliefs():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, subject, predicate, object, payload, confidence, decay_rate, timestamp, status, author_id 
        FROM beliefs WHERE status = 'ACTIVE'
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "subject": row[1],
                "predicate": row[2],
                "object": row[3],
                "payload": row[4],
                "confidence": row[5],
                "decay_rate": row[6],
                "timestamp": row[7],
                "status": row[8],
                "author_id": row[9]
            })
        conn.close()
        return results
        
    @staticmethod
    def delete_belief(belief_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM beliefs WHERE id = ?", (belief_id,))
        conn.commit()
        conn.close()
