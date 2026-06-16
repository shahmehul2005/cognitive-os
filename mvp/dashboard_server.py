import http.server
import socketserver
import os
import sys

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

PORT = int(os.environ.get("PORT", 8000))
PUBLIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))

class StaticDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)
        
    def log_message(self, format, *args):
        # Override to suppress standard console logs so the screen stays clean
        pass

def run_server():
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), StaticDashboardHandler) as httpd:
        print(f"📡 [Dashboard Server] Live visual dashboard active at http://localhost:{PORT}")
        print("💡 Open this URL in your web browser. Press Ctrl+C to terminate server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard server. Goodbye!")

if __name__ == "__main__":
    run_server()
