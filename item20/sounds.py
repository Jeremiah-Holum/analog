"""Synthesized sounds for ITEM 20 that no field recording covers: the show's cheap synth bumper, the
community bulletin board's easy-listening loop, and the phone line (click, dial tone).
    FILM=item20 python3 item20/sounds.py      -> out_item20/sfx/*.wav"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "film"))
import project, sfx

SR = sfx.SR
OUT = os.path.join(project.OUT, "sfx")


def t_(d):
    return np.arange(int(d * SR)) / SR


def hz(note):            # MIDI note -> Hz
    return 440.0 * 2 ** ((note - 69) / 12)


def lowpass(x, a):       # one-pole
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def reverb(x, mix=0.35, delays=(0.031, 0.047, 0.071, 0.113, 0.157), fb=0.55):
    y = x.copy()
    for d in delays:
        k = int(d * SR); z = np.zeros_like(x)
        for rep in range(1, 6):
            if k * rep < len(x):
                z[k * rep:] += x[:len(x) - k * rep] * fb ** rep
        y += z * mix / len(delays) * 2
    return y


def env(n, a=0.01, r=0.3):
    e = np.ones(n)
    ia, ir = int(a * SR), int(r * SR)
    e[:ia] = np.linspace(0, 1, ia)
    e[-ir:] *= np.linspace(1, 0, ir)
    return e


def saw(f, tt, detune=0.004):
    out = 0
    for dt in (-detune, 0, detune):
        ph = (tt * f * (1 + dt)) % 1.0
        out = out + (2 * ph - 1)
    return out / 3


def bumper():
    """'COULEE AFTER DARK': a minor synth stab, a theremin-ish glide, a cheesy thunder crack of noise."""
    d = 6.5
    tt = t_(d); y = np.zeros(len(tt))
    for start, chord in ((0.0, (45, 52, 57, 60, 64)), (1.6, (41, 48, 53, 57, 60)), (3.2, (40, 47, 52, 56, 59))):
        n = int(1.6 * SR) if start < 3 else len(tt) - int(start * SR)
        seg = t_(n / SR)
        s = sum(saw(hz(m), seg) for m in chord) / len(chord)
        s = lowpass(s, 0.08) * env(n, 0.02, 0.4)
        i = int(start * SR); y[i:i + n] += s * 0.5
    th = t_(d)
    glide = 72 + 5 * np.minimum(th / 4.5, 1) + 0.25 * np.sin(2 * np.pi * 5.5 * th)
    ph = np.cumsum(hz(glide)) / SR
    y += 0.18 * np.sin(2 * np.pi * ph) * env(len(th), 0.6, 1.2)
    rng = np.random.default_rng(3)
    crack = lowpass(rng.normal(0, 1, int(1.2 * SR)), 0.05) * np.exp(-np.linspace(0, 6, int(1.2 * SR)))
    y[:len(crack)] += crack * 0.6
    y = reverb(y, 0.45)
    return y / np.abs(y).max() * 0.7


def bbs():
    """The community bulletin board: soft electric-piano chords over a bass, 32 s, loopable."""
    beat = 0.75
    prog = [(48, (60, 64, 67, 71)), (53, (60, 65, 69, 72)), (50, (62, 65, 69, 72)), (55, (59, 62, 65, 67))]
    y = np.zeros(int(32 * SR))
    for bar in range(int(32 / (4 * beat))):
        root, chord = prog[bar % 4]
        i0 = int(bar * 4 * beat * SR)
        n = int(4 * beat * SR)
        seg = t_(n / SR)
        ep = sum(np.sin(2 * np.pi * hz(m) * seg) * np.exp(-seg * 1.6) for m in chord) / 4
        bass = np.sin(2 * np.pi * hz(root - 12) * seg) * np.exp(-seg * 1.2)
        tick = np.zeros(n)
        for b in range(4):
            k = int(b * beat * SR)
            tick[k:k + 600] += np.random.default_rng(bar * 4 + b).normal(0, 1, 600) * np.exp(-np.arange(600) / 80)
        y[i0:i0 + n] += 0.35 * ep + 0.3 * bass + 0.04 * tick
    y = lowpass(y, 0.25)
    return y / np.abs(y).max() * 0.5


def dialtone(d=4.0):
    tt = t_(d)
    return 0.2 * (np.sin(2 * np.pi * 350 * tt) + np.sin(2 * np.pi * 440 * tt)) * env(len(tt), 0.01, 0.05)


def click():
    rng = np.random.default_rng(9)
    n = int(0.08 * SR)
    x = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (0.006 * SR))
    x[:40] += np.linspace(1, -1, 40)
    return lowpass(x, 0.3) * 0.7


def other_voice():
    """Something counting along with Denny, half a beat ahead: his own count, lowered, close and dry, barely there.
    E05..E14 from his C05..C14, and E15 from his final '...fifteen'."""
    import subprocess
    vo = os.path.join(project.OUT, "vo")
    for k, src in [(f"E{i:02d}", f"C{i:02d}") for i in range(5, 15) if i != 10] + [("E15", "D16")]:
        p = os.path.join(vo, src + ".wav")
        if os.path.exists(p):
            subprocess.run(["sox", p, os.path.join(OUT, k + ".wav"), "pitch", "-480", "tempo", "-s", "0.92",
                            "highpass", "180", "lowpass", "3200", "reverb", "8", "20", "20", "gain", "-n", "-20"],
                           check=True, capture_output=True)
            print("wrote", k)


def line_knock():
    """The phone line after Gary hangs up stays open, and three knocks come down it."""
    import subprocess
    src = os.path.join(project.ROOT, "assets", "sfx", "knock_guard.wav")
    subprocess.run(["sox", src, os.path.join(OUT, "line_knock.wav"), "highpass", "320", "lowpass", "3300",
                    "overdrive", "6", "reverb", "30", "gain", "-n", "-14"], check=True, capture_output=True)
    print("wrote line_knock")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("bumper", bumper), ("bbs", bbs), ("dialtone", dialtone), ("hangup", click)):
        sfx.write(os.path.join(OUT, name + ".wav"), fn())
        print("wrote", name)
    other_voice()
    line_knock()


if __name__ == "__main__":
    main()
