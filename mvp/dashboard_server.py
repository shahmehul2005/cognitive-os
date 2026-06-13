import http.server
import socketserver
import json
import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))
from memory_engine import get_connection

PORT = 8000

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
            
            # Fetch semantic memories
            cursor.execute("SELECT memory_id, subject, predicate, object, confidence, provenance, created_at, access_count FROM semantic")
            semantics = []
            for row in cursor.fetchall():
                semantics.append({
                    "id": row[0],
                    "subject": row[1],
                    "predicate": row[2],
                    "object": row[3],
                    "confidence": row[4],
                    "provenance": row[5],
                    "created_at": row[6],
                    "access_count": row[7]
                })
                
            # Fetch episodic memories
            cursor.execute("SELECT memory_id, content, confidence, provenance, created_at, access_count, consolidated FROM episodic")
            episodes = []
            for row in cursor.fetchall():
                try:
                    content = json.loads(row[1])
                except Exception:
                    content = row[1]
                episodes.append({
                    "id": row[0],
                    "content": content,
                    "confidence": row[2],
                    "provenance": row[3],
                    "created_at": row[4],
                    "access_count": row[5],
                    "consolidated": row[6]
                })
                
            conn.close()
            
            self.wfile.write(json.dumps({
                "semantics": semantics,
                "episodes": episodes
            }).encode("utf-8"))
            
        elif self.path == "/api/decisions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT decision_id, content, timestamp FROM decision ORDER BY timestamp DESC")
            decisions = []
            for row in cursor.fetchall():
                try:
                    content = json.loads(row[1])
                except Exception:
                    content = row[1]
                decisions.append({
                    "id": row[0],
                    "content": content,
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
            
            cursor.execute("SELECT COUNT(*) FROM semantic")
            semantic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM episodic")
            episodic_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM decision")
            decision_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_log")
            audit_count = cursor.fetchone()[0]
            
            conn.close()
            
            compression_ratio = 0.0
            total_active = episodic_count + semantic_count
            if total_active > 0:
                compression_ratio = semantic_count / total_active
                
            self.wfile.write(json.dumps({
                "semantic_count": semantic_count,
                "episodic_count": episodic_count,
                "decision_count": decision_count,
                "audit_count": audit_count,
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
