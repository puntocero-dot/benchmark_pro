import os
import threading
import http.server
import socketserver
from price_monitor_v2.main import run_monitor

# Port injected by Railway (or default 8080)
PORT = int(os.environ.get("PORT", 8080))

def start_web_server():
    """Simple HTTP server to serve the dashboard."""
    
    # Ensure a placeholder exists if not yet generated
    if not os.path.exists("dashboard.html"):
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write("<h1>Benchmark Pro is starting...</h1><p>Please refresh in a few minutes.</p>")

    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            # Redirect root to dashboard.html
            if self.path == "/":
                self.path = "/dashboard.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self, self)

    # Use ThreadingTCPServer to prevent blocking if needed (though SimpleHTTP is fast enough for this)
    with socketserver.TCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"🌍 Web server running on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 1. Start Web Server in a background thread
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    # 2. Run the Main Monitor (Blocking)
    print("🚀 Starting Price Monitor V2...")
    run_monitor()
