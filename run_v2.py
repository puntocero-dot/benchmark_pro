import os
import threading
import http.server
import socketserver
import time

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
            # Health Check
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            # Redirect root to dashboard.html
            if self.path == "/":
                self.path = "/dashboard.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self, self)

    # Use ThreadingTCPServer to prevent blocking
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"🌍 Web server running on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    print(f"🚀 Initializing Benchmark Pro on Port {PORT}...")

    # 1. Start Web Server in a background thread (IMMEDIATELY)
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    # Give the thread a moment to bind the socket
    time.sleep(1)

    print("📦 Loading Monitor modules... (This might take a few seconds)")
    try:
        # 2. Deferred Import to prevent blocking server startup
        from price_monitor_v2.main import run_monitor
        
        print("✅ Modules loaded. Starting Monitor Loop...")
        run_monitor()
    except Exception as e:
        print(f"❌ Critical Error starting monitor: {e}")
        # Keep main thread alive so web server doesn't die instantly, allowing us to read logs
        # or serve an error page.
        while True:
            time.sleep(3600)
