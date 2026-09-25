"""Synthesize every sound effect (numpy + sox). Writes out/sfx/<name>.wav, 48 kHz mono."""
import os, subprocess, tempfile, wave
import numpy as np

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "sfx")
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(d * SR)) / SR


def write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def read(path):
    with wave.open(path) as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32767
    if ch == 2:
        x = x.reshape(-1, 2).mean(1)
    assert sr == SR, (path, sr)
    return x


def sox(x, *fx):
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        write(a, x * 0.5)
        subprocess.run(["sox", a, b, *map(str, fx)], check=True, capture_output=True)
        y = read(b) * 2
    return y


def env(n, attack, decay):
    tt = np.arange(n) / SR
    return np.minimum(1, tt / max(attack, 1e-4)) * np.exp(-tt / decay)


def pad(x, d):
    return np.concatenate([x, np.zeros(int(d * SR))])


def mix_at(total, parts):
    y = np.zeros(int(total * SR))
    for off, x, g in parts:
        i = int(off * SR)
        y[i:i + len(x)] += g * x[:len(y) - i]
    return y


def knock(freq=170, weight=1.0):
    n = int(0.25 * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * tt * (1 - 0.15 * tt)) * env(n, 0.001, 0.045 * weight)
    click = rng.normal(0, 1, n) * env(n, 0.0005, 0.006)
    return sox(body * 0.9 + click * 0.35, "lowpass", 2500 * weight)


def knocks(times, freq, weight, room):
    x = mix_at(times[-1] + 1.5, [(tm, knock(freq, weight), 0.9) for tm in times])
    return sox(x, "reverb", room, 50, 80, "gain", -1)


def step(heavy=False):
    n = int(0.18 * SR)
    thud = np.sin(2 * np.pi * (70 if heavy else 95) * np.arange(n) / SR) * env(n, 0.002, 0.03 if heavy else 0.02)
    scuff = rng.normal(0, 1, n) * env(n, 0.004, 0.04)
    x = thud * (1.2 if heavy else 0.7) + sox(scuff, "bandpass", 900, "1.2q") * 0.5
    return sox(x, "lowpass", 3000)


def ding():
    tt = t(2.5)
    x = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((880, 0.6), (1108.7, 0.35), (1760, 0.12)))
    return sox(x * np.exp(-tt / 0.7) * 0.6, "reverb", 30)


def elevator_doors():
    tt = t(2.2)
    rumble = sox(rng.normal(0, 1, len(tt)), "lowpass", 180) * np.sin(np.pi * np.clip(tt / 2.0, 0, 1)) ** 0.5
    thunk = mix_at(2.2, [(0.05, sox(rng.normal(0, 1, 3000) * env(3000, 0.001, 0.01), "lowpass", 400), 1.5)])
    return rumble * 0.8 + thunk


def drone(d=30.0, base=41.0):
    tt = t(d)
    x = np.zeros_like(tt)
    for k, f in enumerate((base, base * 1.007, base * 1.5 * 0.995, base * 2.02, base * 2.99)):
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.05 + 0.03 * k) * tt + k)
        x += np.sin(2 * np.pi * f * tt + 0.3 * np.sin(2 * np.pi * 0.2 * tt)) * lfo / (1 + k * 0.6)
    air = sox(rng.normal(0, 1, len(tt)), "bandpass", 300, "0.5q") * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * tt))
    fade = np.minimum(1, np.minimum(tt / 3, (d - tt) / 3))
    return sox((x * 0.35 + air) * fade, "reverb", 60, "gain", -2)


def stinger(d=3.0, big=False):
    tt = t(d)
    freqs = (55, 58.3, 82.4, 116.5, 123.5, 233) if big else (73.4, 77.8, 110, 155.6)
    x = sum(np.sign(np.sin(2 * np.pi * f * tt)) * 0.2 + np.sin(2 * np.pi * f * 1.003 * tt) * 0.3 for f in freqs)
    x = sox(x, "lowpass", 1800 if big else 1200)
    hit = rng.normal(0, 1, len(tt))
    shape = np.minimum(1, tt / 0.01) * np.exp(-tt / (1.4 if big else 0.9))
    y = (x * 0.5 + sox(hit, "lowpass", 900) * 0.8) * shape
    return sox(y, "overdrive", 12, "reverb", 70, "gain", -1)


def static_burst(d=1.0):
    x = rng.normal(0, 1, int(d * SR))
    return sox(x, "highpass", 400, "lowpass", 9000) * 0.35


def drop():
    parts = [(0.0, sox(rng.normal(0, 1, 5000) * env(5000, 0.001, 0.02), "lowpass", 600), 1.6)]
    for k in range(5):
        parts.append((0.08 + k * 0.05 + rng.uniform(0, 0.04), sox(rng.normal(0, 1, 2000) * env(2000, 0.0005, 0.008), "bandpass", 2500, "2q"), 0.6 / (k + 1)))
    return sox(mix_at(1.2, parts), "reverb", 20)


def drag(d=3.5):
    tt = t(d)
    x = sox(rng.normal(0, 1, len(tt)), "bandpass", 450, "0.8q", "lowpass", 1400)
    am = (0.5 + 0.5 * np.sin(2 * np.pi * 1.1 * tt)) ** 2 * np.minimum(1, np.minimum(tt / 0.4, (d - tt) / 0.8))
    return sox(x * am * 0.8, "reverb", 25)


def breathing(d=10.0, rate=0.9):
    tt = t(d)
    ph = (tt * rate) % 1.0
    inhale = np.where(ph < 0.4, np.sin(np.pi * ph / 0.4), 0)
    exhale = np.where(ph >= 0.45, np.sin(np.pi * (ph - 0.45) / 0.55), 0) * 0.8
    wobble = 1 + 0.2 * np.sin(2 * np.pi * 0.37 * tt)
    n1 = sox(rng.normal(0, 1, len(tt)), "bandpass", 1600, "1.5q")
    n2 = sox(rng.normal(0, 1, len(tt)), "bandpass", 700, "1.2q")
    return sox((n1 * inhale + n2 * exhale) * wobble * 0.5, "lowpass", 4000, "reverb", 10)


def vcr_clunk():
    parts = [(0.0, sox(rng.normal(0, 1, 4000) * env(4000, 0.001, 0.015), "lowpass", 1200), 1.0),
             (0.35, sox(rng.normal(0, 1, 3000) * env(3000, 0.001, 0.01), "bandpass", 1500, "1q"), 0.6)]
    motor = np.sin(2 * np.pi * 180 * t(1.4)) * 0.05 * np.minimum(1, t(1.4) / 0.2)
    return mix_at(2.0, parts + [(0.5, motor, 1.0)])


def tone_1khz(d=1.0):
    return np.sin(2 * np.pi * 1000 * t(d)) * 0.25


BUILD = {
    "knock_guard": lambda: knocks([0, 0.32, 0.64], 190, 0.8, 35),
    "knock_inside": lambda: knocks([0, 0.9, 1.8], 105, 1.6, 55),
    "knock_final": lambda: knocks([0, 1.1, 2.2], 90, 2.0, 70),
    "step": lambda: step(),
    "step2": lambda: step(),
    "step_heavy": lambda: step(True),
    "ding": ding,
    "elev_doors": elevator_doors,
    "drone": lambda: drone(40.0),
    "drone_low": lambda: drone(40.0, 32.7),
    "stinger": lambda: stinger(3.0),
    "stinger_big": lambda: stinger(4.5, True),
    "static": lambda: static_burst(2.0),
    "drop": drop,
    "drag": drag,
    "breath": lambda: breathing(14.0, 0.95),
    "breath_fast": lambda: breathing(10.0, 1.6),
    "vcr": vcr_clunk,
    "tone": tone_1khz,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in BUILD.items():
        write(os.path.join(OUT, name + ".wav"), fn())
    print("sfx:", len(BUILD))
