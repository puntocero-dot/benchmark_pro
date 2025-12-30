import os
import threading
import http.server
import socketserver
import time

# Port injected by Railway (or default 8080)
PORT = int(os.environ.get("PORT", 8080))

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
        
        # Call super implementation
        return super().do_GET()

    def address_string(self):
        # Optim: Disable reverse DNS lookup to prevent lag (499 Errors)
        return self.client_address[0]

def start_monitor_loop():
    """Deferred import and run monitor in background."""
    print("📦 Loading Monitor modules (Background)...")
    try:
        # Deferred Import to prevent slow startup
        from price_monitor_v2.main import run_monitor
        print("✅ Monitor modules loaded. Starting Loop...")
        run_monitor()
    except Exception as e:
        print(f"❌ Critical Error in Monitor Loop: {e}")

if __name__ == "__main__":
    print(f"🚀 Initializing Benchmark Pro on Port {PORT}...")

    # Ensure a placeholder exists if not yet generated
    if not os.path.exists("dashboard.html"):
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write("<h1>Benchmark Pro is starting...</h1><p>Please refresh in a few minutes.</p>")

    # 1. Start Monitor in a background thread (So Web Server gets Main Thread)
    monitor_thread = threading.Thread(target=start_monitor_loop, daemon=True)
    monitor_thread.start()
    
    # 2. Start Web Server in Main Thread (Priority)
    # Use ThreadingTCPServer to handle concurrent requests (Platform + User)
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        print(f"🌍 Web server listening on 0.0.0.0:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("🛑 Server stopping...")
            httpd.shutdown()
