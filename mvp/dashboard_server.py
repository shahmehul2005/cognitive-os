import http.server
import socketserver
import json
import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))
from memory_engine import get_connection

PORT = int(os.environ.get("PORT", 8000))

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to suppress standard console logs so the screen stays clean
        pass
        
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
            with open(html_path, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
                
        elif self.path == "/api/memory":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            # Fetch all active beliefs
            cursor.execute("SELECT id, content, confidence, type, status, provenance, created_at, access_count FROM beliefs WHERE status != 'FORGOTTEN'")
            beliefs = []
            for row in cursor.fetchall():
                beliefs.append({
                    "id": row[0],
                    "content": row[1],
                    "confidence": row[2],
                    "type": row[3],
                    "status": row[4],
                    "provenance": row[5],
                    "created_at": row[6],
                    "access_count": row[7]
                })
                
            # Fetch all edges
            cursor.execute("SELECT source_id, target_id, relation_type, weight, created_at FROM edges")
            edges = []
            for row in cursor.fetchall():
                edges.append({
                    "source": row[0],
                    "target": row[1],
                    "relation_type": row[2],
                    "weight": row[3],
                    "created_at": row[4]
                })
                
            conn.close()
            
            self.wfile.write(json.dumps({
                "nodes": beliefs,
                "edges": edges
            }).encode("utf-8"))
            
        elif self.path == "/api/decisions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, content, created_at FROM beliefs WHERE type = 'DECISION' ORDER BY created_at DESC")
            decisions = []
            for row in cursor.fetchall():
                decisions.append({
                    "id": row[0],
                    "content": row[1],
                    "timestamp": row[2]
                })
            conn.close()
            
            self.wfile.write(json.dumps(decisions).encode("utf-8"))
            
        elif self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT type, COUNT(*) FROM beliefs GROUP BY type")
            counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            semantic_count = counts.get('SEMANTIC', 0)
            episodic_count = counts.get('EPISODIC', 0)
            decision_count = counts.get('DECISION', 0)
            
            cursor.execute("SELECT COUNT(*) FROM edges")
            edge_count = cursor.fetchone()[0]
            
            conn.close()
            
            compression_ratio = 0.0
            total_active = episodic_count + semantic_count
            if total_active > 0:
                compression_ratio = semantic_count / total_active
                
            self.wfile.write(json.dumps({
                "semantic_count": semantic_count,
                "episodic_count": episodic_count,
                "decision_count": decision_count,
                "audit_count": edge_count, # repurpose to edge count
                "compression_ratio": round(compression_ratio, 2)
            }).encode("utf-8"))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run_server():
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"📡 [Dashboard Server] Live visual dashboard active at http://localhost:{PORT}")
        print("💡 Open this URL in your web browser. Press Ctrl+C to terminate server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard server. Goodbye!")

if __name__ == "__main__":
    run_server()
