"""Edit THE THIRD FLOOR: turn renders, stills, voice and sfx into the finished tape.

    python3 film/build.py            # build every segment, then the film
    python3 film/build.py t1_end     # rebuild only segments whose name contains 't1_end', then the film
"""
import math, os, random, subprocess, sys, wave
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timing import FPS, T1_COUNT, T2_COUNT, SHOT_LEN, count_walk
import sfx
from script import VO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
SEG = os.path.join(OUT, "seg")
W, H = 640, 480
SR = sfx.SR
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONO_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
TYPE = "/usr/share/fonts/X11/Type1/c0419bt_.pfb"       # Courier 10 Pitch
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


# ============================================================ images
@lru_cache(64)
def still(name):
    return Image.open(os.path.join(OUT, "stills", name + ".png")).convert("RGB")


@lru_cache(8)
def frame_file(path):
    return Image.open(path).convert("RGB")


def to_screen(img, dx=0.0, dy=0.0, zoom=1.0, cx=None, cy=None):
    """Scale a 384x288 render to 640x480 with a little overscan so it can be shaken or zoomed."""
    sw, sh = img.size
    over = 1.05 * zoom
    cw, ch = sw / over, sh / over
    cx = sw / 2 if cx is None else cx
    cy = sh / 2 if cy is None else cy
    x0 = min(max(cx - cw / 2 + dx * sw / W, 0), sw - cw)
    y0 = min(max(cy - ch / 2 + dy * sh / H, 0), sh - ch)
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def handheld(t, amp=1.0, seed=0):
    """Smooth pseudo-random shake (pixels) for stills that are supposed to be handheld."""
    p = seed * 1.7
    dx = amp * (5 * math.sin(t * 1.3 + p) + 2.5 * math.sin(t * 2.9 + 2 * p) + 1.2 * math.sin(t * 7.1 + p))
    dy = amp * (4 * math.sin(t * 1.1 + 3 * p) + 2 * math.sin(t * 3.7 + p) + 1.0 * math.sin(t * 8.3 + 2 * p))
    return dx, dy


def brightness(img, k):
    if abs(k - 1) < 1e-3:
        return img
    a = np.asarray(img).astype(np.float32) * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ============================================================ overlays
def osd_text(d, xy, s, size=22, anchor="la"):
    f = font(MONO, size)
    x, y = xy
    d.text((x + 2, y + 2), s, font=f, fill=(0, 0, 0), anchor=anchor)
    d.text((x, y), s, font=f, fill=(240, 240, 240), anchor=anchor)


def clock(secs):
    secs = int(secs)
    h, m, s = secs // 3600, (secs // 60) % 60, secs % 60
    return f"{h if h else 12}:{m:02d}:{s:02d} AM"


def cam_osd(img, date, t_clock, play=False):
    d = ImageDraw.Draw(img)
    if date:
        osd_text(d, (38, H - 58), date)
        osd_text(d, (W - 38, H - 58), clock(t_clock), anchor="ra")
    if play:
        osd_text(d, (38, 30), "PLAY ▶")
        osd_text(d, (W - 38, 30), "SP", anchor="ra")
    return img


def cctv_osd(img, label, stamp):
    d = ImageDraw.Draw(img)
    f = font(MONO, 20)
    d.text((22, 18), label, font=f, fill=(235, 235, 235))
    d.text((22, H - 42), stamp, font=f, fill=(235, 235, 235))
    return img


def cctv_stamp(date, secs):
    secs = int(secs)
    return f"{date} {secs // 3600:02d}:{(secs // 60) % 60:02d}:{secs % 60:02d}"


# ============================================================ tape damage (numpy)
class Tape:
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.np = np.random.default_rng(seed)

    def damage(self, img, t, glitch=0.0, wobble=1.0, dropouts=0.12):
        a = np.asarray(img).copy()
        r = self.r
        rows = np.arange(H)
        shift = (wobble * 1.2 * np.sin(rows / 23.0 + t * 6.0)).astype(int)
        # head-switching noise along the bottom edge
        shift[-9:] += (np.array([r.randint(8, 26) for _ in range(9)]))
        if glitch > 0:
            y0 = r.randint(0, H - 40)
            h = int(20 + 140 * glitch * r.random())
            shift[y0:y0 + h] += (glitch * r.uniform(-60, 60) + self.np.normal(0, 8 * glitch, len(shift[y0:y0 + h]))).astype(int)
            if r.random() < glitch:
                roll = int(glitch * r.uniform(0, 80))
                a = np.roll(a, roll, axis=0)
        cols = (np.arange(W)[None, :] - shift[:, None]) % W
        a = a[rows[:, None], cols]
        a[-9:] = np.clip(a[-9:].astype(int) + self.np.integers(-60, 90, (9, W, 1)), 0, 255)
        if glitch > 0:
            band = slice(r.randint(0, H - 30), None)
            a[band][:int(10 + 30 * glitch)] = np.clip(a[band][:int(10 + 30 * glitch)].astype(int) + 70, 0, 255)
        n = 0
        while r.random() < dropouts and n < 3:
            y, x, ln = r.randint(0, H - 1), r.randint(0, W - 50), r.randint(15, 140)
            a[y, x:x + ln] = 235
            n += 1
        return Image.fromarray(a.astype(np.uint8))


def snow(rng):
    small = rng.integers(0, 255, (H // 2, W // 4), dtype=np.uint8)
    img = Image.fromarray(small).resize((W, H), Image.NEAREST).filter(ImageFilter.GaussianBlur(0.6))
    return Image.merge("RGB", (img, img, img))


# ============================================================ ffmpeg styles
STYLE = {
    "cam": ("eq=brightness=-0.07:contrast=1.18:saturation=0.55:gamma=0.82,"
            "colorbalance=rm=0.02:gm=0.05:bm=-0.05:rs=0.03:bs=-0.02,"
            "gblur=sigma=1.3:sigmaV=0.5,rgbashift=rh=3:bh=-3:rv=1,noise=alls=15:allf=t,vignette=PI/4.2"),
    "cctv": "format=gray,eq=contrast=1.35:brightness=-0.03,gblur=sigma=0.9,noise=alls=24:allf=t,format=yuv420p",
    "card": "gblur=sigma=0.8:sigmaV=0.4,rgbashift=rh=2:bh=-2,noise=alls=9:allf=t",
    "clean": "noise=alls=5:allf=t",
}


# ============================================================ audio
@lru_cache(None)
def clip(name):
    for d in ("vo", "sfx"):
        p = os.path.join(OUT, d, name + ".wav")
        if os.path.exists(p):
            return sfx.read(p)
    raise FileNotFoundError(name)


def hiss(n, rng, level=0.012):
    x = rng.normal(0, 1, n)
    x = np.convolve(x, np.ones(6) / 6, "same")
    return x * level * 2.2


def buzz(n, level=0.012, dropouts=None):
    tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 120 * tt) + 0.5 * np.sin(2 * np.pi * 240 * tt) + 0.25 * np.sin(2 * np.pi * 360 * tt)
         + 0.2 * np.sign(np.sin(2 * np.pi * 120 * tt)))
    g = np.ones(n) * level
    if dropouts:
        for fn in dropouts:
            g *= fn(tt)
    return x * g


def room(n, rng, level=0.01):
    x = rng.normal(0, 1, n)
    for _ in range(3):
        x = np.convolve(x, np.ones(40) / 40, "same")
    return x * level * 6


def steps(t0, t1, rate=1.75, heavy=False, gain=0.35, jitter=0.05, fade_to=None):
    out, t, k = [], t0, 0
    while t < t1:
        g = gain if fade_to is None else gain + (fade_to - gain) * (t - t0) / max(t1 - t0, 1e-3)
        out.append((t + random.uniform(-jitter, jitter), ("step_heavy" if heavy else ("step" if k % 2 else "step2")), g))
        t += 1 / rate
        k += 1
    return out


# ============================================================ segments
class Segment:
    """dur in seconds; frame(i, t) -> PIL 640x480; cues [(t, clip, gain)]; bed(n, rng) -> array"""
    def __init__(self, name, dur, frame, style="cam", cues=(), bed=None, glitches=(), tape_seed=0,
                 damage=True, dropouts=0.12):
        self.name, self.dur, self.frame, self.style = name, dur, frame, style
        self.cues, self.bed, self.glitches = list(cues), bed, list(glitches)
        self.tape = Tape(tape_seed or hash(name) % 10000)
        self.damage, self.dropouts = damage, dropouts

    def glitch_at(self, t):
        g = 0.0
        for g0, gd, gs in self.glitches:
            if g0 <= t < g0 + gd:
                g = max(g, gs)
        return g

    def audio(self, path):
        n = int(round(self.dur * SR))
        rng = np.random.default_rng(abs(hash(self.name)) % 2 ** 32)
        y = self.bed(n, rng) if self.bed else np.zeros(n)
        vo_end = -1.0
        for t, name, g in sorted(self.cues, key=lambda c: c[0]):
            x = clip(name)
            if name in VO:  # never let one spoken line talk over the previous one
                if t < vo_end + 0.25:
                    t = vo_end + 0.25
                vo_end = t + len(x) / SR - 0.3
                if vo_end > self.dur:
                    print(f"    ! {self.name}: line {name} runs {vo_end - self.dur:.1f}s past the cut")
            i = max(0, int(t * SR))
            if i >= n:
                continue
            y[i:i + len(x)] += g * x[:n - i]
        for g0, gd, gs in self.glitches:  # tape glitches crackle
            i, j = int(g0 * SR), min(n, int((g0 + gd) * SR))
            if j > i:
                y[i:j] += rng.normal(0, 0.12 * gs, j - i)
        sfx.write(path, np.clip(y, -1, 1))

    def build(self):
        os.makedirs(SEG, exist_ok=True)
        wav = os.path.join(SEG, self.name + ".wav")
        mp4 = os.path.join(SEG, self.name + ".mp4")
        self.audio(wav)
        nf = int(round(self.dur * FPS))
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", wav, "-vf", STYLE[self.style] + ",format=yuv420p",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-c:a", "aac", "-b:a", "192k",
               "-ar", str(SR), "-ac", "2", "-shortest", mp4]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(nf):
            t = i / FPS
            img = self.frame(i, t)
            if img.size != (W, H):
                img = img.resize((W, H))
            if self.damage:
                img = self.tape.damage(img, t, self.glitch_at(t), dropouts=self.dropouts)
            p.stdin.write(img.tobytes())
        p.stdin.close()
        if p.wait():
            raise RuntimeError("ffmpeg failed on " + self.name)
        return mp4


# ------------------------------------------------------------ frame builders
def seq_frames(shot, date, clock0, play=False, hold_first=0.0, hold_last=0.0, play_for=3.0, bright=1.0, zoom=None):
    d = os.path.join(OUT, "frames", shot)
    n = SHOT_LEN[shot]

    def f(i, t):
        k = min(n, max(1, int(round((t - hold_first) * FPS)) + 1))
        img = frame_file(os.path.join(d, f"f_{k:04d}.png"))
        if t < hold_first:
            dx, dy = handheld(t, 0.8, 3)
            img = to_screen(img, dx, dy)
        elif zoom:
            img = to_screen(img, 0, 0, *zoom(t))
        else:
            img = to_screen(img)
        img = brightness(img, bright)
        return cam_osd(img, date, clock0 + t, play and t < play_for)
    return f


def still_frames(schedule, date, clock0, play=False, shake=1.0, seed=0, zoom=None, play_for=3.0):
    """schedule(t) -> (still name, brightness); zoom(t) -> (z, cx, cy) optional"""
    def f(i, t):
        name, k = schedule(t)
        dx, dy = handheld(t, shake, seed)
        if zoom:
            z, cx, cy = zoom(t)
            img = to_screen(still(name), dx, dy, z, cx, cy)
        else:
            img = to_screen(still(name), dx, dy)
        img = brightness(img, k)
        return cam_osd(img, date, clock0 + t, play and t < play_for)
    return f


def flicker(seed, rate, lit, dim, dim_k=1.0, lit_k=1.0, quiet=()):
    """Random fluorescent flicker between two stills. quiet: [(t0,t1)] spans with no flicker."""
    r = random.Random(seed)
    events, t = [], 0.0
    while t < 120:
        t += r.expovariate(rate)
        events.append((t, r.choice([0.05, 0.08, 0.12, 0.2, 0.35])))

    def s(t):
        for a, b in quiet:
            if a <= t < b:
                return (lit, lit_k)
        for e0, ed in events:
            if e0 <= t < e0 + ed:
                return (dim, dim_k)
        return (lit, lit_k)
    return s


def card_frames(lines, size=22, typed=True, cps=45, fontpath=MONO_REG, align="left", fade=0.0, dur=None,
                y_center=True, color=(225, 225, 225)):
    """Text on black, optionally typed out with a blinking cursor."""
    f_ = font(fontpath, size)
    lh = int(size * 1.5)
    total = sum(len(l) for l in lines)
    block_h = lh * len(lines)
    y0 = (H - block_h) // 2 if y_center else 60
    maxw = max(f_.getlength(l) for l in lines) if lines else 0

    def f(i, t):
        img = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(img)
        shown = int(t * cps) if typed else total
        k = 1.0
        if fade and dur:
            k = min(1.0, t / fade, max(0.0, (dur - t) / fade))
        col = tuple(int(c * k) for c in color)
        y, left = y0, shown
        cursor = None
        for line in lines:
            s = line[:max(0, left)]
            left -= len(line)
            x = (W - maxw) / 2 if align == "left" else (W - f_.getlength(line)) / 2
            d.text((x, y), s, font=f_, fill=col)
            if cursor is None and 0 <= left + len(line) <= len(line) and typed:
                cursor = (x + f_.getlength(s), y)
            y += lh
        if typed and (int(t * 2.5) % 2 == 0):
            if cursor is None:
                cursor = (x + f_.getlength(lines[-1]), y - lh)
            d.rectangle([cursor[0] + 2, cursor[1] + 3, cursor[0] + size * 0.6, cursor[1] + size], fill=col)
        return img
    return f


def blue_frames(osd=None, osd_from=0.0):
    def f(i, t):
        img = Image.new("RGB", (W, H), (18, 32, 168))
        if osd and t >= osd_from:
            osd_text(ImageDraw.Draw(img), (38, 30), osd, 26)
        return img
    return f


def static_frames(seed=1):
    rng = np.random.default_rng(seed)
    return lambda i, t: snow(rng)


# ------------------------------------------------------------ beds
def bed(hiss_l=0.012, buzz_l=0.0, room_l=0.006, drone=None, drone_g=0.0, buzz_gate=None):
    def b(n, rng):
        y = hiss(n, rng, hiss_l) + room(n, rng, room_l)
        if buzz_l:
            y += buzz(n, buzz_l, [buzz_gate] if buzz_gate else None)
        if drone:
            x = clip(drone)
            reps = int(np.ceil(n / len(x)))
            y += np.tile(x, reps)[:n] * drone_g
        return y
    return b


def gate_from_schedule(schedule, lit_name):
    def g(tt):
        out = np.ones_like(tt)
        for k in range(0, len(tt), SR // 50):
            out[k:k + SR // 50] = 1.0 if schedule(tt[k])[0] == lit_name else 0.15
        return out
    return g


# ============================================================ the film
def film():
    S = []
    add = S.append
    glitch_in = [(0, 0.3, 0.8)]

    # ---- cold open
    add(Segment("00_play", 3.5, blue_frames("PLAY ▶", 0.9), "clean", [(0.1, "vcr", 0.8)], bed(0.006), damage=False))
    add(Segment("01_static", 0.8, static_frames(1), "clean", [(0, "static", 0.5)], damage=False))
    add(Segment("02_evidence", 16, card_frames([
        "COULEE COUNTY SHERIFF'S DEPARTMENT",
        "EVIDENCE  14-A THROUGH 14-D",
        "",
        "Four (4) VHS-C cassettes recovered from the",
        "security desk of the Brenner Mutual Insurance",
        "building on November 11, 1994.",
        "",
        "Tapes are presented in the order they were",
        "labeled. Nothing has been removed.",
    ], 20), "card", [], bed(0.01, drone="drone_low", drone_g=0.25)))
    add(Segment("03_missing", 10, card_frames([
        "DALE KESSLER, 41, night security officer,",
        "was last seen entering the building",
        "at 10:52 PM on November 9, 1994.",
    ], 20), "card", [], bed(0.01, drone="drone_low", drone_g=0.3)))
    add(Segment("04_static", 0.6, static_frames(2), "clean", [(0, "static", 0.5)], damage=False))

    # ---- TAPE 1
    def label(name, lines, seed):
        return Segment(name, 3.6, card_frames(lines, 22, typed=False, align="center"), "card",
                       [(0, "vcr", 0.5)], bed(0.01))
    add(label("10_label", ["ITEM 14-A", "", "LABEL: \"3RD FL LIGHTS - FOR PRUITT\""], 1))
    date1 = "NOV. 3 1994"
    add(Segment("11_desk", 22, still_frames(lambda t: ("desk_A", 1.0), date1, 7092, play=True, shake=0.12, seed=1),
                "cam", [(1.0, "D01", 1.0), (3.4, "D02", 1.0), (11.0, "D03", 1.0), (16.6, "D04", 1.0)],
                bed(0.012, 0.005), glitches=[(0, 0.5, 1.0), (21.6, 0.4, 0.8)]))
    add(Segment("12_elevator", SHOT_LEN["t1_elevator"] / FPS, seq_frames("t1_elevator", date1, 8045),
                "cam", [(0.35, "ding", 0.6), (1.2, "elev_doors", 0.7), (4.2, "E01", 1.0), (8.2, "E02", 1.0)]
                + steps(7.3, 14, 1.6), bed(0.012, 0.018), glitches=glitch_in))
    add(Segment("13_walk", SHOT_LEN["t1_walk"] / FPS, seq_frames("t1_walk", date1, 8059), "cam",
                [(1.0, "W01", 1.0), (7.5, "W02", 1.0), (15.6, "W03", 1.0)] + steps(0, 20, 1.5),
                bed(0.012, 0.02)))
    hold = 2.6
    t1 = count_walk(T1_COUNT["n"], T1_COUNT["y0"], T1_COUNT["speed"])
    add(Segment("14_count", hold + T1_COUNT["dur"], seq_frames("t1_count", date1, 8200, hold_first=hold), "cam",
                [(0.3, "C00", 1.0)] + [(hold + tt - 0.25, f"N{k + 1:02d}", 1.0) for k, tt in enumerate(t1)]
                + steps(hold, hold + t1[-1] + 0.5, 1.7) + steps(hold + t1[-1] + 0.6, hold + T1_COUNT["dur"] - 0.8, 1.2, gain=0.25),
                bed(0.012, 0.02), glitches=glitch_in))
    end_s = flicker(14, 0.35, "t1_end_lit", "t1_end_dim", quiet=[(12.0, 19.5)])
    end_s2 = lambda t: ("t1_end_dim", 0.8) if 19.6 <= t < 20.4 or 24.9 <= t < 25.1 else end_s(t)
    add(Segment("15_enddoor", 30.6, still_frames(end_s2, date1, 8229, shake=0.9, seed=4), "cam",
                [(0.8, "X01", 1.0), (2.6, "X02", 1.0), (9.4, "X03", 1.0), (12.0, "knock_guard", 0.9),
                 (19.0, "knock_inside", 1.0), (23.6, "X04", 1.0), (26.2, "X05", 1.0)] + steps(0, 0.8, 1.5, gain=0.2),
                bed(0.012, 0.02, buzz_gate=gate_from_schedule(end_s2, "t1_end_lit")), glitches=glitch_in + [(30.3, 0.3, 1.0)]))
    add(Segment("16_static", 1.2, static_frames(3), "clean", [(0, "static", 0.6)], damage=False))

    # ---- TAPE 2
    add(label("20_label", ["ITEM 14-B", "", "LABEL: \"11/7  DOORS\""], 2))
    date2 = "NOV. 7 1994"
    s2 = flicker(21, 0.25, "t2_start_a", "t2_start_b")
    add(Segment("21_start", 13, still_frames(s2, date2, 7770, play=True, shake=0.8, seed=5), "cam",
                [(1.0, "S01", 1.0), (3.0, "S02", 1.0), (8.2, "S03", 1.0)],
                bed(0.012, 0.018, buzz_gate=gate_from_schedule(s2, "t2_start_a")), glitches=[(0, 0.4, 1.0)]))
    t2 = count_walk(T2_COUNT["n"], T2_COUNT["y0"], T2_COUNT["speed"])
    add(Segment("22_count", T2_COUNT["dur"], seq_frames("t2_count", date2, 7785), "cam",
                [(tt - 0.25, f"N{k + 1:02d}", 1.0) for k, tt in enumerate(t2)] + [(32.0, "S04", 1.0)]
                + steps(0, t2[-1] + 0.5, 1.75) + steps(t2[-1] + 0.6, 34.5, 1.1, gain=0.22),
                bed(0.012, 0.016, drone="drone_low", drone_g=0.0), glitches=glitch_in))

    def fig_s(t):
        if t < 10:
            return ("t2_fig_B", 1.0) if (3.0 < t % 4.1 < 3.12) else ("t2_fig_A", 1.0)
        if t < 12:
            return ("t2_fig_A" if int(t * 11) % 3 else "t2_fig_B", 1.0)
        if t < 12.4:
            return ("t2_fig_B", 1.0)
        return ("t2_fig_C", 1.0)
    add(Segment("23_figure", 18.5, still_frames(fig_s, date2, 7821, shake=1.1, seed=6), "cam",
                [(1.2, "F01", 1.0), (3.2, "F02", 1.0), (12.2, "drone", 0.35), (14.6, "F03", 1.0)],
                bed(0.012, 0.014, buzz_gate=gate_from_schedule(fig_s, "t2_fig_A"))))
    add(Segment("24_turn", 3.4, seq_frames("t2_turn", date2, 7840), "cam",
                [(0.55, "stinger_big", 0.9)], bed(0.012, 0.016), glitches=[(2.9, 0.5, 1.0)]))
    add(Segment("25_static", 1.6, static_frames(4), "clean", [(0, "static", 0.8)], damage=False))

    # ---- TAPE 3: building cameras (copied tape)
    add(label("30_label", ["ITEM 14-C", "", "LABEL: \"COPY - BLDG CAMS 11/8\""], 3))

    def cctv_img(name, label_, date, secs, zoom=None):
        img = still(name)
        if zoom:
            z, cx, cy = zoom
            img = img.resize((W, H), Image.BILINEAR, box=(cx - 192 / z, cy - 144 / z, cx + 192 / z, cy + 144 / z))
        else:
            img = img.resize((W, H), Image.BILINEAR)
        return cctv_osd(img, label_, cctv_stamp(date, secs))

    def quad(i, t):
        tt = int(t * 4) / 4
        canvas = Image.new("RGB", (W, H))
        tiles = [("cctv_E", "CAM 01 3F ELEV"), ("cctv_N", "CAM 02 3F CORR N"), ("cctv_S", "CAM 03 3F CORR S"), (None, "CAM 04 STAIR B")]
        f_ = font(MONO, 14)
        for k, (name, lab) in enumerate(tiles):
            x, y = (k % 2) * W // 2, (k // 2) * H // 2
            if name:
                canvas.paste(still(name).resize((W // 2 - 2, H // 2 - 2)), (x + 1, y + 1))
            else:
                ImageDraw.Draw(canvas).text((x + 110, y + 110), "NO SIGNAL", font=font(MONO, 18), fill=(200, 200, 200))
            d = ImageDraw.Draw(canvas)
            d.text((x + 8, y + 6), lab, font=f_, fill=(235, 235, 235))
            d.text((x + 8, y + H // 2 - 22), cctv_stamp("11-08-94", 7980 + tt), font=f_, fill=(235, 235, 235))
        return canvas
    add(Segment("31_quad", 9, quad, "cctv", [], bed(0.008, 0.0, 0.004, "drone_low", 0.3), glitches=[(0, 0.3, 0.6)], dropouts=0.05))

    seq = [  # (still, label, secs, dur, zoom)
        ("cctv_N", "CAM 02 3F CORR N", 8047, 4.5, None),
        ("cctv_N_ajar", "CAM 02 3F CORR N", 8091, 4.0, None),
        ("cctv_N_door", "CAM 02 3F CORR N", 8130, 3.0, None),
        ("cctv_N_door", "CAM 02 3F CORR N  [x4]", 8132, 3.5, (4, 193, 140)),
        ("cctv_N_mid", "CAM 02 3F CORR N", 8158, 3.5, None),
        ("cctv_N_near", "CAM 02 3F CORR N", 8180, 3.0, None),
        ("cctv_E_face", "CAM 01 3F ELEV", 8191, 4.5, None),
        ("cctv_N_open", "CAM 02 3F CORR N", 8200, 3.0, None),
    ]
    starts, acc = [], 0.0
    for s in seq:
        starts.append(acc); acc += s[3]

    def seq_f(i, t):
        k = max(j for j, s0 in enumerate(starts) if s0 <= t)
        name, lab, secs, d, z = seq[k]
        tt = int((t - starts[k]) * 4) / 4
        return cctv_img(name, lab, "11-08-94", secs + tt, z)
    cuts = [(s0, 0.15, 0.7) for s0 in starts[1:]]
    add(Segment("32_cams", acc, seq_f, "cctv", [(starts[6] + 0.05, "stinger", 0.7)],
                bed(0.008, 0.0, 0.004, "drone_low", 0.35), glitches=cuts, dropouts=0.05))
    add(Segment("33_static", 0.8, static_frames(5), "clean", [(0, "static", 0.5)], damage=False))

    # ---- facilities memo
    memo_img = memo_page()

    def memo_f(i, t):
        z = 1.0 + 0.3 * t / 44
        cx, cy = memo_img.width / 2 + 10 * math.sin(t * 0.3), memo_img.height * (0.34 + 0.22 * t / 44)
        dx, dy = handheld(t, 0.6, 9)
        cw, ch = memo_img.width / (1.02 * z), memo_img.width / (1.02 * z) * 0.75
        box = (cx - cw / 2 + dx, cy - ch / 2 + dy, cx + cw / 2 + dx, cy + ch / 2 + dy)
        return memo_img.resize((W, H), Image.BILINEAR, box=box)
    add(Segment("34_memo", 44, memo_f, "cam",
                [(1.5, "M01", 1.0), (9.0, "M02", 1.0), (13.5, "M03", 1.0), (18.0, "M04", 1.0),
                 (25.5, "M05", 1.0), (30.0, "M06", 1.0), (34.5, "M07", 1.0)],
                bed(0.01, 0.0, 0.004, "drone", 0.3), glitches=[(0, 0.4, 0.8), (43.6, 0.4, 1.0)]))
    add(Segment("35_static", 0.6, static_frames(6), "clean", [(0, "static", 0.5)], damage=False))

    # ---- TAPE 4
    add(label("40_label", ["ITEM 14-D", "", "LABEL: \"11/9  IF FOUND GIVE TO POLICE\""], 4))
    date4 = "NOV. 9 1994"
    zoom_desk = lambda t: (1.0 + 1.6 * min(1, max(0, (t - 25.0) / 6)) ** 1.5, 192 + (-104) * min(1, max(0, (t - 25.0) / 6)), 144 + 0 * t)
    add(Segment("41_desk", 36, still_frames(lambda t: ("desk_B", 1.0), date4, 7420, play=True, shake=0.25, seed=7, zoom=zoom_desk),
                "cam", [(1.0, "P01", 1.0), (3.0, "P02", 1.0), (9.0, "P03", 1.0), (14.5, "P04", 1.0),
                        (20.0, "P05", 1.0), (25.5, "P06", 1.0), (31.5, "P07", 1.0)],
                bed(0.012, 0.004, drone="drone_low", drone_g=0.15), glitches=[(0, 0.5, 1.0), (35.6, 0.4, 0.8)]))
    s4 = flicker(41, 0.6, "t4_door_a", "t4_door_b")
    add(Segment("42_door", 14, still_frames(s4, date4, 8470, shake=1.2, seed=8), "cam",
                [(1.0, "G01", 1.0), (3.0, "G02", 1.0), (7.6, "G03", 1.0), (0, "breath", 0.25)],
                bed(0.012, 0.016, buzz_gate=gate_from_schedule(s4, "t4_door_a")), glitches=glitch_in))
    add(Segment("43_enter", SHOT_LEN["t4_enter"] / FPS, seq_frames("t4_enter", date4, 8485, bright=1.25), "cam",
                [(7.0, "O01", 1.0), (12.0, "O02", 1.0), (0, "breath", 0.2)] + steps(0, 13.5, 1.3, gain=0.25),
                bed(0.012, 0.012, 0.01, "drone_low", 0.25), glitches=glitch_in))
    def turn_zoom(t):  # he zooms in on the doorway, then drops the camera
        u = min(1, max(0, (t - 0.8) / 0.5)) if t < 2.3 else max(0, 1 - (t - 2.3) / 0.15)
        return (1 + 1.2 * u, 192 + (186 - 192) * u, 144 + (132 - 144) * u)
    tv_s = lambda t: ("t4_tv_feed", 1.0) if t < 6.9 else ("t4_tv_static", 1.0)
    add(Segment("44_tv", 7.4, still_frames(tv_s, date4, 8501, shake=0.9, seed=9), "cam",
                [(1.2, "V01", 1.0), (3.6, "V02", 1.0), (0, "breath", 0.2)], bed(0.012, 0.0, 0.01, "drone_low", 0.35)))
    add(Segment("45_turn", SHOT_LEN["t4_turn"] / FPS, seq_frames("t4_turn", date4, 8508, bright=1.4, zoom=turn_zoom), "cam",
                [(0.55, "stinger_big", 1.0), (2.45, "drop", 1.0)], bed(0.012, 0.0, 0.01),
                glitches=[(0.4, 0.3, 0.6), (2.4, 0.6, 1.0)]))

    def floor_s(t):  # camera lying on the floor
        if t < 9.5:
            return ("t4_floor_1", 2.0)
        if t < 19.5:
            return ("t4_floor_2", 2.0)
        return ("t4_floor_1", 0.8)
    add(Segment("46_floor", 24.5, still_frames(floor_s, date4, 8512, shake=0.0, seed=10, zoom=lambda t: (1.3, 240, 150)), "cam",
                [(0, "breath_fast", 0.35), (5.8, "step_heavy", 0.4), (7.2, "step_heavy", 0.6), (8.6, "step_heavy", 0.8),
                 (9.4, "stinger", 0.5), (16.2, "drag", 0.9), (21.0, "knock_final", 1.0)],
                bed(0.012, 0.0, 0.01, "drone_low", 0.3), glitches=[(9.4, 0.15, 0.5), (19.4, 0.2, 0.7), (24.0, 0.5, 1.0)]))
    add(Segment("47_stop", 3.0, blue_frames("STOP ■", 0.3), "clean", [(0.2, "vcr", 0.6)], bed(0.004), damage=False))
    add(Segment("48_static", 0.5, static_frames(7), "clean", [(0, "static", 0.4)], damage=False))

    # ---- epilogue
    def end_card(name, lines, dur):
        return Segment(name, dur, card_frames(lines, 21, typed=False, align="center", fade=1.0, dur=dur, fontpath=SERIF),
                       "card", [], bed(0.006, drone="drone_low", drone_g=0.25), damage=False)
    add(end_card("50_end1", ["Dale Kessler has not been located."], 7))
    add(end_card("51_end2", ["Robert Pruitt, facilities manager at Brenner Mutual,", "retired in 1979.", "", "He died in 1983."], 10))
    add(end_card("52_end3", ["The Brenner Mutual building was demolished in 1998.", "",
                             "Floor plans on file with the city list", "nine offices on the third floor."], 10))
    add(end_card("53_end4", ["If you count more than nine, do not continue."], 6))
    add(Segment("54_flash", 0.25, lambda i, t: cctv_img("cctv_E_face", "CAM 01 3F ELEV", "11-09-94", 9999), "cctv",
                [(0, "static", 0.8)], damage=True))
    add(Segment("55_black", 2.0, lambda i, t: Image.new("RGB", (W, H)), "clean", [], None, damage=False))
    add(Segment("56_title", 6.0, card_frames(["THE THIRD FLOOR"], 30, typed=False, align="center", fade=1.2, dur=6.0, fontpath=SERIF),
                "card", [(0.0, "knock_final", 0.5)], bed(0.004), damage=False))
    return S


def memo_page():
    """Photocopied facilities memo."""
    pw, ph = 1000, 1300
    rng = np.random.default_rng(3)
    base = np.full((ph, pw), 214, np.float32) + rng.normal(0, 6, (ph, pw))
    base -= np.linspace(0, 25, pw)[None, :]            # uneven copier light
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(img)
    f, fb = font(TYPE, 30), font(TYPE, 34)
    y = 110
    for line, fnt in [("BRENNER MUTUAL INSURANCE COMPANY", fb), ("FACILITIES NOTICE 71-117", fb), ("", f),
                      ("DATE:  MARCH 12, 1971", f), ("TO:    ALL STAFF AND CONTRACTED SECURITY", f),
                      ("RE:    THIRD FLOOR", f), ("_" * 44, f), ("", f),
                      ("Effective immediately, the third floor", f), ("is closed.", f), ("", f),
                      ("The third floor contains nine (9) offices.", f), ("", f),
                      ("If you count more than nine, do not", f), ("continue. Return to the elevator.", f),
                      ("Do not run.", f), ("", f),
                      ("Do not knock on any door that is not", f), ("numbered.", f), ("", f),
                      ("If something knocks, do not answer.", f), ("", f),
                      ("Do not look at the end of the hall for", f), ("longer than necessary.", f), ("", f), ("", f),
                      ("                         R. PRUITT", f), ("                         FACILITIES", f)]:
        d.text((95, y), line, font=fnt, fill=(28, 26, 30))
        y += 40
    # copier streaks and a coffee ring
    a = np.asarray(img).astype(np.float32)
    for x in rng.integers(0, pw, 5):
        a[:, x:x + rng.integers(1, 4)] *= 0.8
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
    d = ImageDraw.Draw(img)
    d.ellipse([700, 900, 900, 1100], outline=(150, 120, 90), width=6)
    return img


def main():
    only = sys.argv[1:]
    segs = film()
    total = sum(s.dur for s in segs)
    print(f"{len(segs)} segments, {total / 60:.1f} min")
    for s in segs:
        mp4 = os.path.join(SEG, s.name + ".mp4")
        if only and not any(o in s.name for o in only) and (os.path.exists(mp4) or os.environ.get("NOJOIN")):
            continue
        print("  build", s.name, flush=True)
        s.build()
    if os.environ.get("NOJOIN"):
        return
    lst = os.path.join(SEG, "list.txt")
    with open(lst, "w") as f:
        for s in segs:
            f.write(f"file '{s.name}.mp4'\n")
    joined = os.path.join(OUT, "joined.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    final = os.path.join(OUT, "the_third_floor.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", joined, "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-af", "loudnorm=I=-18:TP=-1.5:LRA=14", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final],
                   check=True)
    print("wrote", final)


if __name__ == "__main__":
    main()
