"""
Test HTTP server đơn giản — dùng để test ddoskinhv6.py locally.
Chạy: python3 test_server.py
Mặc định port 8080. Ctrl+C để dừng.
"""
import http.server, threading, time, sys, signal

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

class Handler(http.server.BaseHTTPRequestHandler):
    req_count = 0
    lock = threading.Lock()
    start_time = time.time()

    def do_GET(self):
        with Handler.lock:
            Handler.req_count += 1
            n = Handler.req_count
        elapsed = time.time() - Handler.start_time
        rps = n / max(elapsed, 0.001)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(f"OK req={n} rps={rps:.0f}\n".encode())

    def do_POST(self):
        self.do_GET()

    def log_message(self, fmt, *args):
        pass  # tắt request log — quá nhiều khi bị flood

def _stats():
    prev = 0
    while True:
        time.sleep(5)
        n = Handler.req_count
        elapsed = time.time() - Handler.start_time
        rps = (n - prev) / 5
        prev = n
        print(f"[STATS] total={n:,}  5s_rps={rps:.0f}  elapsed={elapsed:.0f}s")

srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
threading.Thread(target=_stats, daemon=True).start()
print(f"[SERVER] listening on 0.0.0.0:{PORT}")
print(f"[SERVER] target ddos: 127.0.0.1  port: {PORT}")
print(f"[SERVER] Ctrl+C để dừng\n")
try:
    srv.serve_forever()
except KeyboardInterrupt:
    print(f"\n[SERVER] Stopped. Total req: {Handler.req_count:,}")
