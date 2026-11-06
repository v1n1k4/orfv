import math as m
import random
import time
import bisect
import tkinter as tk
import tkinter.font as tkf

SIZE = 8
FPS = 30
D2R = m.pi / 180

T_ENV_IN = 1.6
T_CUR0 = 1.9
T_CUR1 = 4.1
T_CLICK = 4.55
T_BURN = T_CLICK + 0.12
T_SPREAD = 3.4
T_R0 = T_BURN + 2.3
T_FORM = 3.8
T_MEET0 = T_R0 + T_FORM - 0.25
T_MEET_DUR = 3.4
T_GLOW = T_R0 + 1.8
T_FIRE_END = T_BURN + T_SPREAD + 2.2

rng = random.Random(21)

root = tk.Tk()
root.title("愛してる、そして永遠に愛し続けるよ、アッシュ | For You, Ash")
root.resizable(False, False)
root.bind("<Escape>", lambda e: root.destroy())

fams = set(tkf.families())
MONO = next((f for f in ("Cascadia Mono", "Consolas", "Courier New", "DejaVu Sans Mono", "Courier")
             if f in fams), "Courier")
scr_h = root.winfo_screenheight()
fnt = tkf.Font(root=root, family=MONO, size=SIZE, weight="bold")
CH = fnt.metrics("linespace")
CW = fnt.measure("M")
ROWS = int(max(30, min(46, (scr_h - 140) // CH)))
COLS = int(ROWS * CH / CW)
W, H = COLS * CW, ROWS * CH
S = H / 640.0
root.geometry(f"{W}x{H}+{(root.winfo_screenwidth() - W) // 2}+{max(0, (scr_h - H) // 2 - 20)}")

BG = (0.010, 0.007, 0.012)


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def mix(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)


def sc(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


_hx = {}
LV = 40


def hexc(c):
    k = (int(clamp(c[0]) * (LV - 0.01)), int(clamp(c[1]) * (LV - 0.01)), int(clamp(c[2]) * (LV - 0.01)))
    s = _hx.get(k)
    if s is None:
        s = "#%02x%02x%02x" % tuple(int(v * 255 / (LV - 1)) for v in k)
        _hx[k] = s
    return s


cv = tk.Canvas(root, width=W, height=H, bg=hexc(BG), highlightthickness=0)
cv.pack()

_P = list(range(256))
rng.shuffle(_P)
_N = [rng.uniform(-1, 1) for _ in range(256)]


def vn(x, y):
    xi = int(m.floor(x))
    yi = int(m.floor(y))
    xf = x - xi
    yf = y - yi
    xi &= 255
    yi &= 255
    x1 = (xi + 1) & 255
    y1 = (yi + 1) & 255
    u = xf * xf * (3 - 2 * xf)
    v = yf * yf * (3 - 2 * yf)
    a = _N[_P[(_P[xi] + yi) & 255]]
    b = _N[_P[(_P[x1] + yi) & 255]]
    c = _N[_P[(_P[xi] + y1) & 255]]
    d = _N[_P[(_P[x1] + y1) & 255]]
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v


def nz(t, a=1.0):
    return (m.sin(t * 2.1 * a) + 0.7 * m.sin(t * 3.3 * a + 1.7) + 0.4 * m.sin(t * 5.7 * a + 0.6)) / 2.1


HS = [[rng.random() for _ in range(COLS)] for _ in range(ROWS)]
HS2 = [[rng.random() for _ in range(COLS)] for _ in range(ROWS)]


def ramp_lut(stops, n=64):
    out = []
    for i in range(n):
        v = i / (n - 1)
        for k in range(len(stops) - 1):
            a, ca = stops[k]
            b, cb = stops[k + 1]
            if v <= b:
                out.append(mix(ca, cb, (v - a) / (b - a)))
                break
    return out


FIRE = [
    (0.00, (0.30, 0.01, 0.00)),
    (0.18, (0.78, 0.05, 0.01)),
    (0.38, (1.00, 0.24, 0.02)),
    (0.60, (1.00, 0.52, 0.05)),
    (0.80, (1.00, 0.80, 0.26)),
    (1.00, (1.00, 0.98, 0.82)),
]
LUT = ramp_lut(FIRE)

REDS = [
    (0.00, (0.10, 0.00, 0.02)),
    (0.22, (0.34, 0.01, 0.05)),
    (0.45, (0.66, 0.04, 0.09)),
    (0.68, (0.90, 0.09, 0.15)),
    (0.88, (1.00, 0.24, 0.26)),
    (1.00, (1.00, 0.55, 0.52)),
]
RLUT = ramp_lut(REDS)
RCH = "-=+*#%&@8"
SMOKE_C = (0.50, 0.44, 0.44)

BLUES = [
    (0.00, (0.05, 0.01, 0.02)),
    (0.26, (0.28, 0.02, 0.05)),
    (0.52, (0.68, 0.10, 0.11)),
    (0.78, (0.96, 0.46, 0.20)),
    (1.00, (1.00, 0.90, 0.68)),
]
BLUE = ramp_lut(BLUES)

CX = W / 2.0
EW = 0.76 * W
EH = 0.74 * EW
ECY = 0.55 * H
EX0, EX1 = CX - EW / 2, CX + EW / 2
EY0, EY1 = ECY - EH / 2, ECY + EH / 2
FLAP_H = 0.50 * EH
TIPY = EY0 + FLAP_H
HR = 0.062 * H
HCY = TIPY - 0.25 * HR
XPL, XPR = CX - 0.17 * EW, CX + 0.17 * EW
YPL = EY0 + FLAP_H * (1 - 0.17 * EW / (EW / 2))
IGX, IGY = CX, HCY

GLYPH = {
    "F": ["###", "#..", "##.", "#..", "#.."],
    "O": ["###", "#.#", "#.#", "#.#", "###"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    " ": ["...", "...", "...", "...", "..."],
}
TEXT = "FOR YOU"
TXT = ["", "", "", "", ""]
for _i, _ch in enumerate(TEXT):
    for _k in range(5):
        TXT[_k] += GLYPH[_ch][_k] + ("." if _i < len(TEXT) - 1 else "")
TW = len(TXT[0])
TC0 = int(CX / CW - TW)
TR0 = int((HCY + 1.2 * HR) / CH) + 2


def ink(r, c):
    px = (c - TC0) // 2
    py = r - TR0
    return c >= TC0 and 0 <= px < TW and 0 <= py < 5 and TXT[py][px] == "#"


PAPER = "#%&@8"
FLAPC = (0.91, 0.81, 0.64)
BODYC = (0.85, 0.74, 0.56)
SIDEC = (0.76, 0.64, 0.47)
BOTC = (0.85, 0.74, 0.56)
INK = (0.18, 0.06, 0.05)
INKT = (0.26, 0.06, 0.05)
STRIPE = ((0.78, 0.12, 0.14), (0.92, 0.74, 0.32), (0.32, 0.05, 0.07))


def heart_f(hx, hy, s):
    X = hx / s
    Y = (hy - 0.25) / s + 0.25
    return (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3


def in_seal(x, y):
    hx_ = (x - CX) / HR
    hy_ = (HCY - y) / HR
    return -1.4 < hx_ < 1.4 and -1.3 < hy_ < 1.6 and heart_f(hx_, hy_, 1.0) <= 0


def env_style(r, c, x, y, hs, hs2):
    if x < EX0 or x > EX1 or y < EY0 or y > EY1:
        return None
    hx_ = (x - CX) / HR
    hy_ = (HCY - y) / HR
    if -1.4 < hx_ < 1.4 and -1.3 < hy_ < 1.6 and heart_f(hx_, hy_, 1.0) <= 0:
        k = clamp(0.5 - 0.30 * hx_ + 0.28 * hy_)
        if heart_f(hx_, hy_, 0.88) > 0:
            return ("#", (0.86, 0.64, 0.24))
        if heart_f(hx_, hy_, 0.68) > 0:
            return ("&%#"[int(hs * 3) % 3], mix((0.78, 0.12, 0.14), (0.98, 0.38, 0.26), k))
        if (hx_ + 0.38) ** 2 + (hy_ - 0.58) ** 2 < 0.048:
            return ("*", (1.0, 0.92, 0.68))
        return ("@%"[hs2 > 0.80], mix((0.64, 0.07, 0.09), (0.95, 0.26, 0.22), k))
    if ink(r, c):
        return ("@", INKT)
    if ink(r - 1, c - 1):
        return ("%", (0.58, 0.42, 0.26))
    if abs(y - HCY) < 0.52 * CH and abs(x - CX) > 1.05 * HR and EX0 + 2 * CW < x < EX1 - 2 * CW:
        return ("=", (0.92, 0.74, 0.30) if (c + r) % 3 == 0 else (0.78, 0.12, 0.14))
    fh = FLAP_H * (1 - abs(x - CX) / (EW / 2))
    dfl = EY0 + fh - y
    if abs(dfl) < 0.45 * CH:
        return ("\\" if x < CX else "/", INK)
    side = False
    if dfl < 0:
        if x <= XPL:
            yl = EY1 + (YPL - EY1) * (x - EX0) / (XPL - EX0)
            if abs(y - yl) < 0.45 * CH:
                return ("/", INK)
            side = y < yl
        elif x >= XPR:
            yr = YPL + (EY1 - YPL) * (x - XPR) / (EX1 - XPR)
            if abs(y - yr) < 0.45 * CH:
                return ("\\", INK)
            side = y < yr
    if (x < EX0 + 1.3 * CW or x > EX1 - 1.3 * CW or y < EY0 + 0.9 * CH or y > EY1 - 0.9 * CH):
        return ("+" if (c + r) % 2 == 0 else "*", STRIPE[((c + r) % 6) // 2])
    base = FLAPC if dfl >= 0 else (SIDEC if side else BOTC)
    k = (1.05 - 0.18 * (y - EY0) / EH) * (0.90 + 0.20 * hs2)
    if dfl < 0 and dfl > -1.4 * CH:
        k *= 0.74 + 0.20 * (-dfl) / (1.4 * CH)
    elif 0.45 * CH < dfl < 1.4 * CH:
        k *= 1.06
    return (PAPER[int(hs * len(PAPER)) % len(PAPER)], (base[0] * k, base[1] * k, base[2] * k))


raw = []
SHD = []
for r in range(ROWS):
    y = (r + 0.5) * CH
    for c in range(COLS):
        x = (c + 0.5) * CW
        s_ = env_style(r, c, x, y, HS[r][c], HS2[r][c])
        if s_ is not None:
            raw.append((r, c, s_[0], s_[1], x, y))
        elif EX0 + 0.9 * CW <= x <= EX1 + 1.8 * CW and EY0 + 0.8 * CH <= y <= EY1 + 2.0 * CH:
            SHD.append((r, c, x, y))
MAXD = max(m.hypot(e[4] - IGX, e[5] - IGY) for e in raw)
ENVC = []
SEALC = []
for r, c, ch, col, x, y in raw:
    d = m.hypot(x - IGX, y - IGY)
    nzv = vn(x * 0.035 + 4, y * 0.035 + 9) * 0.5 + 0.5
    tb = T_SPREAD * (d / MAXD) ** 0.92 + 0.6 * nzv * min(1.0, d / (0.12 * H))
    ENVC.append((r, c, ch, col, tb, HS[r][c], HS2[r][c], x, y))
    if in_seal(x, y):
        SEALC.append((r, c))
ENV_SORTED = sorted(ENVC, key=lambda e: e[4])
TBS = [e[4] for e in ENV_SORTED]
SHDC = []
for r, c, x, y in SHD:
    d = m.hypot(x - IGX, y - IGY)
    tb = T_SPREAD * (d / MAXD) ** 0.92
    ex = max(0.0, x - EX1, EX0 - x)
    ey = max(0.0, y - EY1, EY0 - y)
    f = 1 - clamp(m.hypot(ex, ey) / (2.0 * CW))
    SHDC.append((r, c, ":" if f > 0.45 else ".", sc((0.12, 0.08, 0.06), 0.35 + 0.65 * f), tb, HS[r][c]))

BED = []
RB0 = int(EY1 / CH) + 1
for rr_ in (RB0, RB0 + 1):
    if rr_ >= ROWS:
        continue
    for c in range(COLS):
        x = (c + 0.5) * CW
        u = 1 - ((x - CX) / (EW * 0.50)) ** 2
        if u > 0.12:
            BED.append((rr_, c, u ** 0.5, HS[rr_][c], rr_ == RB0))

VINI_UP = "VINI"
VINI_LO = "vini"
ASH_UP = "ASH"
ASH_LO = "ash"

SUN_GOLD = [
    (0.00, (0.52, 0.18, 0.01)),
    (0.24, (0.84, 0.42, 0.02)),
    (0.52, (0.98, 0.68, 0.05)),
    (0.78, (1.00, 0.88, 0.18)),
    (1.00, (1.00, 0.97, 0.58)),
]
SLUT = ramp_lut(SUN_GOLD)

SUN_DISK = [
    (0.00, (0.12, 0.05, 0.01)),
    (0.38, (0.28, 0.12, 0.03)),
    (0.72, (0.55, 0.28, 0.05)),
    (1.00, (0.92, 0.64, 0.12)),
]
DLUT = ramp_lut(SUN_DISK)

RX = CX
SR = 0.142 * H
RR = 0.136 * H
SY_C = 0.340 * H
RY_C = 0.350 * H
RY = SY_C
STEM_Y0 = SY_C + 0.84 * SR
STEM_Y1 = 0.905 * H
TOP_Y = SY_C - 1.20 * SR
STEM_HW = 0.88 * CW
T_MEET0 = T_R0 + T_FORM - 0.25
T_MEET_DUR = 3.4

GREEN_D = (0.03, 0.15, 0.06)
GREEN_L = (0.16, 0.48, 0.20)


def contrast(I):
    return clamp(0.52 + (I - 0.45) * 1.45)


def leaf_hit(dx, dy, ax, ay, ang, L, Wd, bend):
    ca, sa = m.cos(ang * D2R), m.sin(ang * D2R)
    lx, ly = dx - ax, dy - ay
    s = (lx * ca - ly * sa) / L
    if s < 0 or s > 1:
        return None
    v = lx * sa + ly * ca - bend * L * s * s
    w = Wd * m.sin(m.pi * (s ** 0.7)) * (1 + 0.07 * m.sin(s * 38))
    if w <= 0.25 or abs(v) > w:
        return None
    return s, v / w


SUN_SEPALS = [
    (-0.45, 0.88, 220, 0.75, 0.12, -0.08),
    (0.45, 0.88, -40, 0.75, 0.12, 0.08),
    (0.00, 0.96, 270, 0.65, 0.11, 0.00),
]


def sunflower_head_sample(dx, dy):
    ex, ey = dx / SR, dy / (SR * 0.94)
    r = m.hypot(ex, ey)
    if r <= 1.24:
        th = m.atan2(ey, ex)
        disk_r = 0.43 + 0.015 * m.cos(14 * th)
        if r <= disk_r:
            u = r / disk_r
            s1 = m.sin(u * 18.0 + th * 8.0)
            s2 = m.sin(u * 18.0 - th * 5.0)
            pat = 0.5 + 0.25 * s1 + 0.25 * s2
            return ("sun_disk", u, pat, th)
        n_pet = 16
        s_in = ((th * n_pet) / (2 * m.pi)) % 1.0
        prof_in = max(0.0, m.sin(m.pi * s_in)) ** 1.35
        r_in_max = disk_r - 0.04 + (1.16 - disk_r) * prof_in
        if r <= r_in_max and prof_in > 0.12:
            w = clamp((r - disk_r) / max(0.05, r_in_max - disk_r))
            return ("sun_petal", 1, w, (s_in - 0.5) * 2.0, th)
        s_out = ((th * n_pet) / (2 * m.pi) + 0.5) % 1.0
        prof_out = max(0.0, m.sin(m.pi * s_out)) ** 1.45
        r_out_max = disk_r - 0.04 + (0.98 - disk_r) * prof_out
        if r <= r_out_max and prof_out > 0.15:
            w = clamp((r - disk_r) / max(0.05, r_out_max - disk_r))
            return ("sun_petal", 0, w, (s_out - 0.5) * 2.0, th)
    for ax, ay, ang, L, Wd, bend in SUN_SEPALS:
        h_ = leaf_hit(dx, dy, ax * SR, ay * SR, ang, L * SR, Wd * SR, bend)
        if h_:
            return ("sun_sepal", h_[0], h_[1])
    return None


def sunflower_style(smp, hs, hs2, r, c):
    kind = smp[0]
    ch_up, ch_lo = VINI_UP[c % 4], VINI_LO[c % 4]
    if kind == "sun_disk":
        _, u, pat, th = smp
        lit = 0.5 + 0.5 * m.cos(th + 2.2)
        I = (0.20 + 0.48 * pat + 0.25 * (u * u)) * (0.78 + 0.36 * lit)
        if u > 0.78:
            I = clamp(I + 0.32 * ((u - 0.78) / 0.22))
        I = clamp(I * (0.90 + 0.20 * hs))
        return (ch_up if I > 0.62 else ch_lo), DLUT[int(I * 63)]
    if kind == "sun_petal":
        _, ring, w, v, th = smp
        base_i = 0.44 if ring == 1 else 0.30
        ridge = 1.0 - 0.35 * abs(v)
        lit = 0.5 + 0.5 * m.cos(th + 2.2)
        I = contrast(clamp((base_i + 0.46 * (w ** 0.85)) * ridge * (0.76 + 0.38 * lit) * (0.94 + 0.12 * hs)))
        if hs2 > 0.985 and w > 0.5:
            return ch_up, (1.0, 0.98, 0.75)
        return (ch_up if I >= 0.45 else ch_lo), SLUT[int(I * 63)]
    s, v = smp[1], smp[2]
    t_ = (clamp(1 - abs(v)) ** 1.2) * 0.8 + 0.2 * hs
    return (ch_up if t_ >= 0.5 else ch_lo), mix(GREEN_D, GREEN_L, clamp(t_ * (0.75 + 0.25 * s)))


LAYERS = [
    (1.00, 5, 0.00, 0.17),
    (0.82, 5, 0.90, 0.16),
    (0.65, 4, 1.70, 0.15),
    (0.49, 3, 2.40, 0.13),
]
LBASE = [0.34, 0.40, 0.46, 0.52]
SPIR_R = 0.30
ROSE_SEPALS = [
    (-0.55, 0.96, 212, 0.94, 0.13, -0.10),
    (-0.22, 1.06, 245, 0.84, 0.11, -0.08),
    (0.55, 0.96, -32, 0.94, 0.13, 0.10),
    (0.22, 1.06, -65, 0.84, 0.11, 0.08),
    (0.00, 1.10, 270, 0.68, 0.10, 0.00),
]


def layer_b(k, th):
    R, n, ph, amp = LAYERS[k]
    s = ((th + ph) * n / (2 * m.pi)) % 1.0
    return R * (1 - amp * (1 - s ** 0.55)), s


def rose_head_sample(dx, dy):
    for ax, ay, ang, L, Wd, bend in ROSE_SEPALS:
        h_ = leaf_hit(dx, dy, ax * RR, ay * RR, ang, L * RR, Wd * RR, bend)
        if h_:
            return ("rose_sepal", h_[0], h_[1])
    ex, ey = dx / RR, dy / (RR * 0.84)
    uu = m.hypot(ex, ey)
    if uu <= 1.18:
        th = m.atan2(ey, ex)
        Rth = 1 + 0.045 * m.cos(5 * th + 0.7) + 0.03 * m.cos(8 * th + 2.1)
        u = uu / Rth
        if u <= 1.0:
            if u < SPIR_R:
                return ("rose_spiral", u / SPIR_R, th)
            for k in range(len(LAYERS) - 1, -1, -1):
                b, _ = layer_b(k, th)
                if u <= b:
                    return ("rose_petal", k, u, th)
    cx2, cy2 = dx / (RR * 0.78), (dy - RR * 0.68) / (RR * 0.70)
    if cx2 * cx2 + cy2 * cy2 <= 1:
        return ("rose_cup", cx2, cy2)
    rx_, ry_ = dx / (RR * 0.20), (dy - RR * 1.32) / (RR * 0.18)
    if rx_ * rx_ + ry_ * ry_ <= 1:
        return ("rose_recept", rx_, ry_)
    return None


def rose_style(smp, hs, hs2, r=0, c=0):
    kind = smp[0]
    ch_up, ch_lo = ASH_UP[c % 3], ASH_LO[c % 3]
    if kind == "rose_spiral":
        _, u, th = smp
        p = u * 2.6 + th / (2 * m.pi)
        f = p - m.floor(p)
        I = 0.26 + 0.62 * (f ** 1.3)
        if f < 0.16:
            I *= 0.25 + f * 4.7
        I *= 0.60 + 0.40 * u
        I *= 0.74 + 0.52 * (0.5 + 0.5 * m.cos(th + 2.36))
        I = contrast(clamp(I * (0.94 + 0.12 * hs)))
        return (ch_up if I >= 0.46 else ch_lo), RLUT[int(I * 63)]
    if kind == "rose_petal":
        _, k, u, th = smp
        b, s = layer_b(k, th)
        w = u / b
        I = LBASE[k] + 0.30 * w * w
        if w > 0.88:
            I += 0.34 * (w - 0.88) / 0.12
        bn = layer_b(k + 1, th)[0] if k + 1 < len(LAYERS) else SPIR_R
        g = u - bn
        if g < 0.10:
            I *= 0.25 + 7.5 * max(0.0, g)
        if s < 0.16:
            I *= 0.40 + 3.75 * s
        elif s > 0.92:
            I += 0.12
        I *= 0.72 + 0.56 * (0.5 + 0.5 * m.cos(th + 2.36))
        I = contrast(clamp(I * (0.94 + 0.12 * hs)))
        if hs2 > 0.985 and w > 0.5:
            return ch_up, (1.0, 0.72, 0.66)
        return (ch_up if I >= 0.46 else ch_lo), RLUT[int(I * 63)]
    if kind == "rose_cup":
        _, cx2, cy2 = smp
        seam = abs(m.sin((cx2 * 1.6 + cy2 * 0.4) * m.pi * 1.5))
        I = (0.36 - 0.20 * cx2 - 0.08 * cy2) * (0.55 + 0.45 * (seam ** 0.6)) * (1 - 0.28 * (cx2 * cx2 + cy2 * cy2))
        I = contrast(clamp(I * (0.9 + 0.2 * hs)))
        return (ch_up if I >= 0.46 else ch_lo), RLUT[int(I * 63)]
    if kind == "rose_recept":
        return ch_up, mix((0.06, 0.20, 0.08), (0.14, 0.42, 0.17), clamp(0.5 - 0.5 * smp[1]))
    s, v = smp[1], smp[2]
    t_ = (clamp(1 - abs(v)) ** 1.2) * 0.8 + 0.2 * hs
    return (ch_up if t_ >= 0.5 else ch_lo), mix(GREEN_D, GREEN_L, clamp(t_ * (0.75 + 0.25 * s)))


def get_flower_pose(u_unite):
    sep = (0.235 * (1 - u_unite) + 0.128 * u_unite) * W
    tilt_s = -9.0 * u_unite * D2R
    tilt_r = 9.0 * u_unite * D2R
    return (CX - sep, SY_C, CX + sep, RY_C, m.cos(tilt_s), m.sin(tilt_s), m.cos(tilt_r), m.sin(tilt_r))


def stems_at(y, u_unite, sx_c, rx_c):
    f = clamp((y - STEM_Y0) / (STEM_Y1 - STEM_Y0))
    pull = u_unite * ease(min(1.0, f * 2.1))
    braid_amp = u_unite * (0.019 * W) * ease(min(1.0, f * 2.4))
    braid_ph = f * m.pi * 3.4
    braid = braid_amp * m.sin(braid_ph)
    z_ord = m.cos(braid_ph)
    wave = (1 - u_unite * 0.65) * 0.011 * W * m.sin(f * 5.2)
    return sx_c * (1 - pull) + CX * pull + braid + wave, rx_c * (1 - pull) + CX * pull - braid - wave, f, z_ord


def sample_scene_at(r, c, x, y, u_unite, pose):
    sx_c, sy_c, rx_c, ry_c, cos_s, sin_s, cos_r, sin_r = pose
    hs, hs2 = HS[r][c], HS2[r][c]
    dxs, dys = x - sx_c, y - sy_c
    smp_s = sunflower_head_sample(dxs * cos_s - dys * sin_s, dxs * sin_s + dys * cos_s)
    dxr, dyr = x - rx_c, y - ry_c
    smp_r = rose_head_sample(dxr * cos_r - dyr * sin_r, dxr * sin_r + dyr * cos_r)
    if smp_s and smp_r:
        if (dxr * dxr) / (RR * RR) + (dyr * dyr) / (RR * RR) < (dxs * dxs) / (SR * SR) + (dys * dys) / (SR * SR):
            ch, col = rose_style(smp_r, hs, hs2, r, c)
            return ch, col, "ash"
        ch, col = sunflower_style(smp_s, hs, hs2, r, c)
        return ch, col, "vini"
    if smp_r:
        ch, col = rose_style(smp_r, hs, hs2, r, c)
        return ch, col, "ash"
    if smp_s:
        ch, col = sunflower_style(smp_s, hs, hs2, r, c)
        return ch, col, "vini"
    if STEM_Y0 - 0.1 * SR <= y <= STEM_Y1:
        ssx, srx, f, z_ord = stems_at(y, u_unite, sx_c, rx_c)
        hit_s = abs(x - ssx) <= STEM_HW
        hit_r = abs(x - srx) <= STEM_HW
        if hit_s or hit_r:
            if hit_s and (not hit_r or z_ord >= 0):
                v = (x - ssx) / STEM_HW
                return (VINI_UP if (r + c) % 2 == 0 else VINI_LO)[r % 4], mix(GREEN_D, (0.22, 0.56, 0.18), clamp(0.55 - 0.45 * v)), "vini"
            v = (x - srx) / STEM_HW
            return (ASH_UP if (r + c) % 2 == 0 else ASH_LO)[r % 3], mix(GREEN_D, GREEN_L, clamp(0.50 - 0.45 * v)), "ash"
        if u_unite > 0.55 and abs(f - 0.34) < 0.045 and abs(x - 0.5 * (ssx + srx)) <= 2.2 * CW:
            uk = (u_unite - 0.55) / 0.45
            col = mix((0.85, 0.10, 0.14), (1.0, 0.78, 0.32), (r + c) % 2)
            return (VINI_UP[c % 4] if c % 2 == 0 else ASH_UP[c % 3]), sc(col, uk), "knot"
        ly_s1 = STEM_Y0 + 0.32 * (STEM_Y1 - STEM_Y0)
        s1 = stems_at(ly_s1, u_unite, sx_c, rx_c)[0]
        lh_s1 = leaf_hit(x, y, s1, ly_s1, 152, 1.15 * SR, 0.30 * SR, 0.14)
        if lh_s1:
            ch, col = sunflower_style(("sun_leaf", lh_s1[0], lh_s1[1]), hs, hs2, r, c)
            return ch, col, "vini"
        ly_r1 = STEM_Y0 + 0.36 * (STEM_Y1 - STEM_Y0)
        r1 = stems_at(ly_r1, u_unite, sx_c, rx_c)[1]
        lh_r1 = leaf_hit(x, y, r1, ly_r1, 28, 1.12 * RR, 0.28 * RR, -0.14)
        if lh_r1:
            ch, col = rose_style(("rose_leaf", lh_r1[0], lh_r1[1]), hs, hs2, r, c)
            return ch, col, "ash"
    if u_unite > 0.35:
        kh = ease((u_unite - 0.35) / 0.65)
        hx, hy = (x - CX) / (0.37 * W), (0.45 * H - y) / (0.36 * H)
        if -1.35 < hx < 1.35 and -1.25 < hy < 1.55 and heart_f(hx, hy, 1.0) <= 0 and heart_f(hx, hy, 0.91) >= 0:
            is_left = x < CX
            ch = VINI_UP[(c + r) % 4] if is_left else ASH_UP[(c + r) % 3]
            bcol = (1.0, 0.82, 0.22) if is_left else (1.0, 0.28, 0.32)
            return ch, sc(bcol, 0.55 + 0.45 * kh), "heart"
    return None


POSE0 = get_flower_pose(0.0)
POSE1 = get_flower_pose(1.0)
ROSEMASK = set()
HALO = set()
for r in range(ROWS):
    y = (r + 0.5) * CH
    for c in range(COLS):
        x = (c + 0.5) * CW
        if sample_scene_at(r, c, x, y, 1.0, POSE1) is not None:
            ROSEMASK.add((r, c))
for r_, c_ in ROSEMASK:
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            q = (r_ + dr, c_ + dc)
            if q not in ROSEMASK:
                HALO.add(q)

TK_MAP = [[0.0] * COLS for _ in range(ROWS)]
RP = []
for r in range(ROWS):
    y = (r + 0.5) * CH
    key_y = clamp((y - TOP_Y) / (STEM_Y1 - TOP_Y))
    for c in range(COLS):
        tk_ = T_R0 + 0.1 + key_y * T_FORM + HS[r][c] * 0.38
        TK_MAP[r][c] = tk_
        x = (c + 0.5) * CW
        smp0 = sample_scene_at(r, c, x, y, 0.0, POSE0)
        if smp0 is not None:
            ch, _, tag = smp0
            lim = tk_ - T_BURN - 0.85
            n = bisect.bisect_right(TBS, lim)
            src = ENV_SORTED[rng.randrange(max(1, n))]
            sx_, sy_ = src[7], src[8]
            ts = min(max(T_BURN + src[4] + 0.1, tk_ - 2.1), tk_ - 0.72)
            dx_, dy_ = x - sx_, y - sy_
            dd = m.hypot(dx_, dy_) + 1e-6
            RP.append((ts, tk_, sx_, sy_, x, y, -dy_ / dd, dx_ / dd,
                       rng.uniform(-0.12, 0.12) * dd, rng.uniform(0.05, 0.13) * H, rng.uniform(0, 6.28), ch))


def fpos(f, s):
    ts, tk_, sx_, sy_, tx, ty, nx, ny, amp, lift, ph, _ = f
    e = s * s * (3 - 2 * s)
    sn = m.sin(m.pi * s)
    x = sx_ + (tx - sx_) * e + nx * amp * sn + 3.0 * S * m.sin(s * 13 + ph) * (1 - s)
    y = sy_ + (ty - sy_) * e + ny * amp * sn - lift * sn
    return x, y


LX, LY = RX, RY
NB = 720
BGE = []
for r in range(ROWS):
    y = (r + 0.5) * CH
    for c in range(COLS):
        if (r, c) in ROSEMASK:
            continue
        x = (c + 0.5) * CW
        dx_, dy_ = x - LX, y - LY
        a_ = m.atan2(dy_, dx_)
        dn = m.hypot(dx_, dy_) / (0.55 * H)
        ab = int(((a_ + m.pi) / (2 * m.pi)) * NB) % NB
        BGE.append((r, c, ab, dn, (r, c) in HALO))
NCH = 3
BGCH = [BGE[i::NCH] for i in range(NCH)]
BGC = {}
RAYF = [0.0] * NB
RAYM = [0.0] * NB
LIGHTC = (0.55, 0.75, 1.0)
WHITE = (0.95, 0.98, 1.0)
BGRAMP = ".:-=+*#"


def bg_tables(tt):
    for i in range(NB):
        a = -m.pi + (i + 0.5) * (2 * m.pi / NB)
        r1 = (0.5 + 0.5 * m.sin(a * 23 + 1.6 * m.sin(a * 3 + tt * 0.15) + tt * 0.10)) ** 6
        r2 = (0.5 + 0.5 * m.sin(a * 47 - tt * 0.12 + 1.5 * m.sin(a * 5 - tt * 0.10))) ** 9
        r3 = (0.5 + 0.5 * m.sin(a * 11 + tt * 0.08)) ** 4
        RAYF[i] = 0.55 * r1 + 0.50 * r2 + 0.20 * r3
        mn = 0.0
        for k in range(8):
            d = abs((a - k * m.pi / 4 + m.pi) % (2 * m.pi) - m.pi)
            if d < 0.3:
                mn += (1.0 if k % 2 == 0 else 0.65) * m.exp(-(d / 0.045) ** 2) * (0.88 + 0.12 * m.sin(tt * 0.9 + k * 1.3))
        RAYM[i] = mn


def bg_eval(e, tt, gt):
    r, c, ab, dn, halo = e
    core = m.exp(-dn * 2.8)
    glow = m.exp(-dn * 1.3)
    I = (0.95 * core + 0.16 * glow
         + 0.62 * RAYF[ab] * m.exp(-dn * 1.9)
         + 0.85 * RAYM[ab] * m.exp(-dn * 1.05)) * gt
    if halo:
        I *= 0.22
    if I < 0.05:
        return None
    I = min(I, 1.3)
    ch = BGRAMP[min(len(BGRAMP) - 1, int(I * len(BGRAMP) * 0.8))]
    return ch, BLUE[int(clamp(I) * 63)]


MOTES = [[rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.01, 0.04) * H, rng.uniform(0, 6.28),
          rng.uniform(0.5, 1.0)] for _ in range(46)]
STARS = []
for _ in range(60):
    rr_, cc_ = rng.randrange(ROWS), rng.randrange(COLS)
    if (rr_, cc_) not in ROSEMASK:
        STARS.append((rr_, cc_, rng.uniform(0, 6.28), rng.uniform(0.6, 2.2)))


def draw_ambient(t, dt, gt, new):
    base = 0.20 + 0.80 * gt
    for rr, cc, ph, sp in STARS:
        v = 0.5 + 0.5 * m.sin(t * sp + ph)
        if v > 0.35:
            a = base * (v - 0.35) / 0.65
            ch = "*" if v > 0.9 else "+" if v > 0.7 else "."
            new[(rr, cc)] = (ch, sc(mix((0.70, 0.85, 1.0), WHITE, v), 0.25 + 0.75 * a))
    if gt < 0.02:
        return
    for p in MOTES:
        p[1] -= p[2] * dt
        p[0] += 6 * S * m.sin(t * 0.8 + p[3]) * dt
        if p[1] < -4:
            p[1] = H + 4
            p[0] = rng.uniform(0, W)
        rr, cc = int(p[1] // CH), int(p[0] // CW)
        if 0 <= rr < ROWS and 0 <= cc < COLS and (rr, cc) not in ROSEMASK:
            v = gt * p[4] * (0.5 + 0.5 * m.sin(t * 1.7 + p[3]))
            if v > 0.12:
                new[(rr, cc)] = ("." if v < 0.5 else ":", sc(mix(LIGHTC, WHITE, p[4]), 0.4 + 0.6 * v))


ARW = [(0.0, 0.0), (0.0, 0.86), (0.19, 0.69), (0.31, 0.99), (0.44, 0.93), (0.32, 0.65), (0.58, 0.65)]
PH_ = 0.21 * H
POLY = [(x * PH_, y * PH_) for x, y in ARW]


def _pip(px, py):
    ins = False
    j = len(POLY) - 1
    for i in range(len(POLY)):
        xi, yi = POLY[i]
        xj, yj = POLY[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi:
            ins = not ins
        j = i
    return ins


def _pdist(px, py):
    best = 1e9
    for i in range(len(POLY)):
        ax, ay = POLY[i]
        bx, by = POLY[(i + 1) % len(POLY)]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy + 1e-9
        t_ = clamp(((px - ax) * vx + (py - ay) * vy) / L2)
        d = m.hypot(px - (ax + vx * t_), py - (ay + vy * t_))
        if d < best:
            best = d
    return best


CUR_FILL, CUR_EDGE, CUR_GLOW, CUR_SHAD = [], [], [], []
_occ = set()
_NC, _NR = int(0.58 * PH_ / CW) + 3, int(PH_ / CH) + 3
for j in range(_NR):
    for i in range(_NC):
        cin = core = 0
        for sy in (1 / 6, 3 / 6, 5 / 6):
            for sx in (1 / 6, 3 / 6, 5 / 6):
                px, py = (i + sx) * CW, (j + sy) * CH
                if _pip(px, py):
                    cin += 1
                    if _pdist(px, py) > 0.9 * CW:
                        core += 1
        cxm, cym = (i + 0.5) * CW, (j + 0.5) * CH
        h_ = ((j * 7 + i * 13) % 10) / 10.0
        if core >= 5:
            t_ = clamp((cym / PH_) * 0.85 + (cxm / (0.58 * PH_)) * 0.15)
            col = mix((0.52, 0.22, 0.97), (1.0, 0.42, 0.74), t_)
            bev = _pdist(cxm, cym) < 1.8 * CW
            if bev:
                col = mix(col, (1.0, 0.92, 1.0), 0.20)
            CUR_FILL.append((j, i, "%" if bev else "@", col, h_))
            _occ.add((j, i))
        elif cin >= 3:
            CUR_EDGE.append((j, i, h_))
            _occ.add((j, i))
        else:
            d = _pdist(cxm, cym)
            if d < 1.9 * CW:
                CUR_GLOW.append((j, i, 1 - d / (1.9 * CW), h_))
for (j, i) in list(_occ):
    if (j + 1, i + 1) not in _occ:
        CUR_SHAD.append((j + 1, i + 1))

TGX, TGY = CX - 0.004 * W, HCY - 0.015 * H


def cursor_pos(t):
    s = clamp((t - T_CUR0) / (T_CUR1 - T_CUR0))
    k = 1 - (1 - s) ** 3.5
    p0 = (1.10 * W, 0.04 * H)
    p1 = (0.95 * W, 0.80 * H)
    p2 = (0.64 * W, 0.78 * H)
    p3 = (TGX, TGY)
    u = 1 - k
    x = u ** 3 * p0[0] + 3 * u * u * k * p1[0] + 3 * u * k * k * p2[0] + k ** 3 * p3[0]
    y = u ** 3 * p0[1] + 3 * u * u * k * p1[1] + 3 * u * k * k * p2[1] + k ** 3 * p3[1]
    return x, y


items = {}
prev = {}
sparks = []
smoke = []
bits = []
st = {"burst": False, "click": False, "hot": False, "united": False}
HEAT = [[0.0] * COLS for _ in range(ROWS + 2)]
FSET = {1: ".'", 2: ":.", 3: "^'", 4: "^*", 5: "*(", 6: "(+)", 7: "%&", 8: "#%", 9: "#@", 10: "@"}
frame = [0]


def bed_k(t):
    a = clamp((t - (T_BURN + 0.25)) / 1.2)
    b = clamp((t - (T_BURN + T_SPREAD + 0.6)) / 1.6)
    return ease(a) * (1 - ease(b))


def fire_step(src, t):
    out = {}
    if not src and not st["hot"]:
        return out
    last = COLS - 1
    rnd = rng.random
    fr = frame[0]
    anyhot = False
    for r in range(ROWS):
        row, b1, b2 = HEAT[r], HEAT[r + 1], HEAT[r + 2]
        for c in range(COLS):
            q = rnd()
            w = c - 1 if q < 0.27 else c + 1 if q > 0.73 else c
            if w < 0:
                w = 0
            elif w > last:
                w = last
            cl = c - 1 if c > 0 else 0
            cr = c + 1 if c < last else last
            v = (b1[w] * 2 + b1[cl] + b1[cr] + b2[c]) * 0.2 - (0.030 + 0.062 * ((q * 7.0) % 1.0))
            row[c] = v if v > 0 else 0.0
    for (r, c), v in src.items():
        if v > HEAT[r][c]:
            HEAT[r][c] = v
    for r in range(ROWS):
        row = HEAT[r]
        for c in range(COLS):
            v = row[c]
            if v > 0.10:
                anyhot = True
                i = min(10, int(v * 10.5))
                s_ = FSET[i]
                out[(r, c)] = (s_[(c * 3 + r * 7 + fr) % len(s_)], LUT[int(clamp(v) * 63)])
            elif v > 0.01:
                anyhot = True
    st["hot"] = anyhot
    return out


def draw_cursor(t, new):
    a = clamp((t - T_CUR0) / 0.3)
    bt = t - T_BURN
    if a <= 0 or bt > 1.1:
        return
    px, py = cursor_pos(t)
    c0, r0 = int(px // CW), int(py // CH)
    press = T_CLICK <= t < T_CLICK + 0.20
    if press:
        c0 += 1
        r0 += 1
    bk = clamp(bt) if bt > 0 else 0.0
    if T_CUR0 < t < T_CUR1 + 0.15:
        for q in range(1, 11):
            tx_, ty_ = cursor_pos(t - 0.05 * q)
            rr, cc = int(ty_ // CH), int(tx_ // CW)
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                v = (1 - q / 11.0) * 0.8
                new[(rr, cc)] = ("+" if q < 4 else ".", (0.58 * v, 0.24 * v, 0.95 * v))
    for j, i in CUR_SHAD:
        rr, cc = r0 + j, c0 + i
        if 0 <= rr < ROWS and 0 <= cc < COLS and bk < 0.5:
            und = new.get((rr, cc))
            ucol = und[1] if und else BG
            new[(rr, cc)] = (":", mix(ucol, (0.03, 0.01, 0.06), 0.65 * a))
    for j, i, g, hh in CUR_GLOW:
        rr, cc = r0 + j, c0 + i
        if 0 <= rr < ROWS and 0 <= cc < COLS and hh < 0.7 and bk < 0.6:
            v = a * g * (1 - bk) * 0.85
            new[(rr, cc)] = (":" if g > 0.5 else ".", (0.55 * v, 0.18 * v, 0.78 * v))
    for j, i, hh in CUR_EDGE:
        if hh < bk:
            continue
        rr, cc = r0 + j, c0 + i
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            col = (0.98, 0.86, 1.0)
            if press:
                col = (1.0, 1.0, 1.0)
            if bk > 0:
                col = mix(col, LUT[int(clamp(0.55 + 0.4 * (1 - hh)) * 63)], clamp(bk * 1.6))
            new[(rr, cc)] = ("#", sc(col, a))
    for j, i, ch, col, hh in CUR_FILL:
        if hh < bk:
            continue
        rr, cc = r0 + j, c0 + i
        if not (0 <= rr < ROWS and 0 <= cc < COLS):
            continue
        if press:
            col = mix(col, (1.0, 0.96, 1.0), 0.55)
        if bk > 0:
            col = mix(col, LUT[int(clamp(0.55 + 0.4 * (1 - hh)) * 63)], clamp(bk * 1.6))
        new[(rr, cc)] = (ch, sc(col, a))


def _ring_cells(cx, cy, pad):
    for rr in range(max(0, int((cy - pad) // CH)), min(ROWS, int((cy + pad) // CH) + 1)):
        y = (rr + 0.5) * CH
        for cc in range(max(0, int((cx - pad) // CW)), min(COLS, int((cx + pad) // CW) + 1)):
            yield rr, cc, (cc + 0.5) * CW, y


def draw_click(t, dt, new):
    a = t - T_CLICK
    if not st["click"] and a >= 0:
        st["click"] = True
        for _ in range(52):
            ang = rng.uniform(0, 2 * m.pi)
            sp = rng.uniform(120, 560) * S
            bits.append([TGX, TGY, m.cos(ang) * sp, m.sin(ang) * sp, 0.0, rng.uniform(0.5, 1.1)])
    if a < 0 or a > 1.2:
        return
    if a < 0.25:
        k = a / 0.25
        rad = 0.03 * H + 0.05 * H * k
        for rr, cc, x, y in _ring_cells(TGX, TGY, rad + CW):
            d = m.hypot(x - TGX, y - TGY)
            if d < rad:
                v = (1 - k) * (1 - d / rad * 0.5)
                und = new.get((rr, cc))
                col = mix((1.0, 0.9, 1.0), (0.85, 0.5, 1.0), k)
                new[(rr, cc)] = ("@" if v > 0.5 else "#", mix(und[1], col, clamp(v * 1.3)) if und else sc(col, v))
    for d0, c0_, c1_ in ((0.0, (0.65, 0.30, 1.0), (1.0, 0.55, 0.9)),
                         (0.13, (0.55, 0.25, 0.95), (1.0, 0.65, 0.95)),
                         (0.26, (0.50, 0.30, 1.0), (1.0, 0.85, 1.0))):
        aa = a - d0
        if aa < 0 or aa > 0.9:
            continue
        k = aa / 0.9
        rad = 0.02 * H + 0.26 * H * (1 - (1 - k) ** 2.2)
        th = (1.7 - 1.0 * k) * CW
        al = (1 - k) ** 1.2
        col = mix(c0_, c1_, k)
        for rr, cc, x, y in _ring_cells(TGX, TGY, rad + th):
            q = abs(m.hypot(x - TGX, y - TGY) - rad) / th
            if q >= 1:
                continue
            v = (1 - q) * al * 1.5
            c2 = sc(col, clamp(v))
            und = new.get((rr, cc))
            if und:
                c2 = mix(und[1], col, clamp(v * 0.85))
            new[(rr, cc)] = ("O" if q < 0.35 else "o" if q < 0.65 else ".", c2)
    if a < 0.55:
        k = a / 0.55
        l0 = 0.03 * H + 0.05 * H * k
        l1 = 0.06 * H + 0.24 * H * (1 - (1 - k) ** 2)
        steps = int((l1 - l0) / (CW * 0.9)) + 1
        for n in range(14):
            ang = n * 2 * m.pi / 14 + 0.2
            ca, sa = m.cos(ang), m.sin(ang)
            chr_ = "-" if abs(ca) > 0.92 else "|" if abs(sa) > 0.92 else ("\\" if ca * sa > 0 else "/")
            for s_ in range(steps):
                f = s_ / steps
                dist = l0 + (l1 - l0) * f
                rr, cc = int((TGY + sa * dist) // CH), int((TGX + ca * dist) // CW)
                if 0 <= rr < ROWS and 0 <= cc < COLS:
                    v = (1 - k) * (1 - 0.6 * f)
                    new[(rr, cc)] = (chr_, sc(mix((1.0, 0.9, 1.0), (0.7, 0.35, 1.0), f), clamp(v * 1.3)))
    alive = []
    for b in bits:
        b[4] += dt
        if b[4] >= b[5]:
            continue
        b[2] *= (1 - 2.0 * dt)
        b[3] = b[3] * (1 - 2.0 * dt) + 60 * S * dt
        b[0] += b[2] * dt
        b[1] += b[3] * dt
        k = b[4] / b[5]
        rr, cc = int(b[1] // CH), int(b[0] // CW)
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            new[(rr, cc)] = ("*" if k < 0.4 else "+" if k < 0.7 else ".",
                             sc(mix((1.0, 0.92, 1.0), (0.62, 0.28, 0.95), k), 1 - 0.5 * k))
        alive.append(b)
    bits[:] = alive


def render(t, dt):
    global prev
    frame[0] += 1
    new = {}
    gt = ease((t - T_GLOW) / 3.6)

    if gt > 0.003:
        if frame[0] % NCH == 0 or BGC == {}:
            bg_tables(t)
        for e in BGCH[frame[0] % NCH]:
            res = bg_eval(e, t, gt)
            if res:
                BGC[(e[0], e[1])] = res
            else:
                BGC.pop((e[0], e[1]), None)
        new.update(BGC)
    draw_ambient(t, dt, gt, new)

    tbn = t - T_BURN
    pin = clamp(t / T_ENV_IN)

    for r, c, ch, col, tb, hs in SHDC:
        if tbn - tb >= 0:
            continue
        vis = pin * 1.3 - hs * 0.5
        if vis > 0:
            new[(r, c)] = (ch, sc(col, min(1.0, vis * 1.6)))

    front = []
    src = {}
    rnd = rng.random
    for r, c, ch, col, tb, hs, hs2, x, y in ENVC:
        tau = tbn - tb
        if tau >= 1.35:
            continue
        if tau < 0:
            vis = pin * 1.3 - hs * 0.5
            if vis <= 0:
                continue
            k = min(1.0, vis * 1.6)
            if tbn > 0 and tau > -0.5:
                w = (tau + 0.5) * 2.0
                col = mix(col, (0.30, 0.10, 0.03), w * 0.75)
                if w > 0.6:
                    col = mix(col, (1.0, 0.38, 0.05), (w - 0.6) * 1.3)
            new[(r, c)] = (ch, (col[0] * k, col[1] * k, col[2] * k))
            continue
        if tau < 0.50:
            src[(r, c)] = 0.72 + 0.28 * rnd()
        elif tau < 0.95:
            src[(r, c)] = (0.45 + 0.15 * rnd()) * (1 - (tau - 0.50) / 0.45)
        if tau < 0.38:
            q = tau / 0.38
            T = clamp(0.98 - 0.62 * q + 0.14 * nz(t * 9 + hs * 20))
            ch2 = ("@#&%" if q < 0.6 else "#%=+")[int(hs2 * 4) % 4]
            new[(r, c)] = (ch2, LUT[int(T * 63)])
            front.append((x, y))
        else:
            a = 1 - (tau - 0.38) / 0.97
            if hs2 > a ** 0.7:
                continue
            if ((hs * 37.0 + t * 1.6) % 1.0) > 0.84 - 0.08 * a:
                new[(r, c)] = ("*", LUT[int(clamp(0.28 + 0.5 * a) * 63)])
            else:
                kk = 0.45 + 0.9 * a
                new[(r, c)] = ("%#="[int(hs * 3) % 3], (0.13 * kk, 0.07 * kk, 0.05 * kk))

    if T_CUR1 - 0.3 <= t < T_BURN + 0.02:
        if t < T_CLICK:
            k = 0.28 * ease((t - (T_CUR1 - 0.3)) / 0.3) * (0.8 + 0.2 * m.sin(t * 9))
            mf = lambda col: mix(col, (1.0, 0.85, 1.0), k)
        elif t < T_CLICK + 0.20:
            mf = lambda col: sc(col, 0.62)
        else:
            k = 0.7 * (1 - clamp((t - T_CLICK - 0.2) / 0.15))
            mf = lambda col: mix(col, (1.0, 0.9, 0.8), k)
        for key in SEALC:
            v = new.get(key)
            if v:
                new[key] = (v[0], mf(v[1]))

    bk = bed_k(t)
    if bk > 0.01:
        for rr, cc, shp, hs, top in BED:
            fl = 0.5 + 0.5 * m.sin(t * 6 + hs * 40)
            T = clamp(bk * shp * (0.25 + 0.45 * fl + 0.2 * hs))
            if T > 0.08:
                new[(rr, cc)] = ("=%#@"[int(hs * 4) % 4], LUT[int(T * 63)])
            if top:
                src[(rr, cc)] = bk * shp * (0.50 + 0.38 * rnd())
        for rr, cc, shp, hs, top in BED:
            if top and rnd() < 0.5 * dt * 10 * bk * shp:
                front.append(((cc + 0.5) * CW, (rr + 0.5) * CH))

    new.update(fire_step(src, t))

    rim = 0.65 * gt
    u_unite = ease((t - T_MEET0) / T_MEET_DUR)
    pose = get_flower_pose(u_unite)

    if t >= T_R0:
        for r in range(ROWS):
            y_ = (r + 0.5) * CH
            tk_row = TK_MAP[r]
            for c in range(COLS):
                tk_ = tk_row[c]
                if t < tk_:
                    continue
                x_ = (c + 0.5) * CW
                cell = sample_scene_at(r, c, x_, y_, u_unite, pose)
                if not cell:
                    continue
                ch, col, tag = cell
                hs = HS[r][c]
                heat = 1.0 - (t - tk_)
                if heat > 0 and u_unite < 0.05:
                    hh = heat ** 1.4
                    col = mix(col, LUT[int(clamp(0.35 + 0.65 * hh) * 63)], clamp(hh * 1.15))
                    if hh > 0.5:
                        ch = ch.upper()
                elif tag == "heart":
                    pulse = 0.65 + 0.35 * m.sin(t * 3.0 + (r + c) * 0.25)
                    col = sc(col, pulse)
                elif u_unite > 0.8 and hs > 0.92 and m.sin(t * 3.2 + hs * 40) > 0.86:
                    ch, col = ch.upper(), mix(col, (1.0, 0.96, 0.80), 0.55)
                new[(r, c)] = (ch, col)

    if u_unite >= 0.72 and not st["united"]:
        st["united"] = True
        for _ in range(95):
            a_ = rng.uniform(0, 2 * m.pi)
            sp_ = rng.uniform(45, 290) * S
            sparks.append([CX, RY + 0.05 * H, m.cos(a_) * sp_, m.sin(a_) * sp_ - 40 * S,
                           0.0, rng.uniform(0.9, 2.2), -22 * S])

    for f in RP:
        ts, tk_ = f[0], f[1]
        if t < ts or t >= tk_:
            continue
        s = (t - ts) / (tk_ - ts)
        tch = f[11]
        for lag, chh, dim in ((0.0, tch.upper(), 1.0), (0.06, tch.lower(), 0.8), (0.12, ".", 0.6)):
            ss = s - lag
            if ss < 0:
                break
            x_, y_ = fpos(f, ss)
            rr, cc = int(y_ // CH), int(x_ // CW)
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                T = clamp((0.45 + 0.55 * s) * dim)
                new[(rr, cc)] = (chh, LUT[int(T * 63)])

    if t >= T_BURN and not st["burst"]:
        st["burst"] = True
        for _ in range(150):
            a_ = rng.uniform(-170, -10) * D2R
            sp_ = rng.uniform(100, 560) * S
            sparks.append([IGX, IGY, m.cos(a_) * sp_, m.sin(a_) * sp_, 0.0,
                           rng.uniform(0.6, 1.6), -rng.uniform(20, 120) * S])
    if front and t < T_FIRE_END:
        n = int(380 * dt * min(1.0, len(front) / 50.0) + rng.random())
        for _ in range(n):
            x_, y_ = front[rng.randrange(len(front))]
            a_ = rng.uniform(-125, -55) * D2R
            sp_ = rng.uniform(60, 360) * S
            sparks.append([x_, y_, m.cos(a_) * sp_, m.sin(a_) * sp_, 0.0,
                           rng.uniform(0.7, 1.9), -rng.uniform(25, 140) * S])
        if rng.random() < 22 * dt:
            x_, y_ = front[rng.randrange(len(front))]
            smoke.append([x_, y_ - 0.05 * H, rng.uniform(-6, 6) * S, -rng.uniform(25, 55) * S, 0.0,
                          rng.uniform(1.8, 3.2), rng.uniform(0, 6.28), SMOKE_C])
    if t > T_R0 + T_FORM and gt > 0.2:
        for _ in range(int(7 * dt + rng.random())):
            sparks.append([CX + rng.uniform(-1.35, 1.35) * RR, RY + rng.uniform(-0.85, 1.05) * RR,
                           rng.uniform(-14, 14) * S, -rng.uniform(25, 70) * S, 0.0,
                           rng.uniform(1.2, 2.4), -8 * S])
    if len(sparks) > 1600:
        del sparks[:len(sparks) - 1600]

    alive = []
    for s in sparks:
        s[4] += dt
        if s[4] >= s[5]:
            continue
        s[2] = s[2] * (1 - 1.3 * dt) + 55 * S * m.sin(s[4] * 7 + s[5] * 20) * dt
        s[3] += s[6] * dt
        s[0] += s[2] * dt
        s[1] += s[3] * dt
        k = 1 - s[4] / s[5]
        rr, cc = int(s[1] // CH), int(s[0] // CW)
        if 0 <= rr < ROWS and 0 <= cc < COLS:
            new[(rr, cc)] = ("*" if k > 0.55 else "+" if k > 0.30 else ".",
                             LUT[int(clamp(0.15 + 0.85 * k) * 63)])
        alive.append(s)
    sparks[:] = alive

    alive = []
    for s in smoke:
        s[4] += dt
        if s[4] >= s[5]:
            continue
        k = s[4] / s[5]
        s[0] += (s[2] + 14 * S * m.sin(s[4] * 2.2 + s[6])) * dt
        s[1] += s[3] * dt
        al = m.sin(m.pi * k) * 0.5
        rr, cc = int(s[1] // CH), int(s[0] // CW)
        if al > 0.10 and 0 <= rr < ROWS and 0 <= cc < COLS:
            und = new.get((rr, cc))
            ucol = und[1] if und else BG
            new[(rr, cc)] = (".:;+"[min(3, int(al * 7))], mix(ucol, s[7], al))
        alive.append(s)
    smoke[:] = alive

    draw_click(t, dt, new)
    draw_cursor(t, new)

    out = {k: (v[0], hexc(v[1])) for k, v in new.items()}
    for key, val in out.items():
        if prev.get(key) != val:
            it = items.get(key)
            if it is None:
                items[key] = cv.create_text((key[1] + 0.5) * CW, (key[0] + 0.5) * CH,
                                            text=val[0], fill=val[1], font=fnt, anchor="center")
            else:
                cv.itemconfig(it, text=val[0], fill=val[1])
    for key in prev.keys() - out.keys():
        cv.itemconfig(items[key], text=" ")
    prev = out


state = {"t0": time.perf_counter(), "last": 0.0}


def restart(_=None):
    state["t0"] = time.perf_counter()
    state["last"] = 0.0
    st["burst"] = False
    st["click"] = False
    st["hot"] = False
    st["united"] = False
    sparks.clear()
    smoke.clear()
    bits.clear()
    BGC.clear()
    for row in HEAT:
        for i in range(COLS):
            row[i] = 0.0
    for p in MOTES:
        p[1] = rng.uniform(0, H)


root.bind("r", restart)
root.bind("R", restart)


def tick():
    t0 = time.perf_counter()
    t = t0 - state["t0"]
    dt = clamp(t - state["last"], 0.0, 0.1)
    state["last"] = t
    render(t, dt)
    el = (time.perf_counter() - t0) * 1000
    root.after(max(1, int(1000 / FPS - el)), tick)


root.after(100, tick)
root.mainloop()