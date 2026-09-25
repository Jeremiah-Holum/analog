"""Build the films' sound effects from real recordings (Freesound, all CC0) instead of synthesis.

Clips come from the freesound-laion-640k dataset (Hugging Face, benjamin-paine/freesound-laion-640k);
see film/SOUND.md for the list. Run with the Chatterbox venv (needs librosa):
    /home/user/tts/cb/bin/python film/realsfx.py
Writes out/sfx/<name>.wav (48 kHz mono), replacing the synthesized versions of the same names.
Drones and stingers stay synthesized (they're score, not sound effects)."""
import os, subprocess, tempfile
import numpy as np
import librosa
import sfx

CLIPS = "/home/user/sfxlib/clips"
SR = sfx.SR


def load(fid):
    y, _ = librosa.load(os.path.join(CLIPS, f"{fid}.wav"), sr=SR, mono=True)
    return y / (np.abs(y).max() + 1e-9)


def hits(y, top_db=28, min_gap=0.12):
    """Onsets of individual hits (knocks, steps), as sample indices."""
    on = librosa.onset.onset_detect(y=y, sr=SR, units="samples", backtrack=True, delta=0.2)
    out = []
    for o in on:
        if not out or o - out[-1] > min_gap * SR:
            out.append(int(o))
    return out


def cut(y, a, b, fade=0.004):
    s = y[max(0, a):b].copy()
    n = max(1, int(fade * SR))
    s[:n] *= np.linspace(0, 1, n)
    s[-n:] *= np.linspace(1, 0, n)
    return s


def trim(y, top_db=35):
    t, _ = librosa.effects.trim(y, top_db=top_db)
    return t


def loudest_window(y, dur):
    """The dur-second stretch of y with the most energy (for picking the busy part of a long clip)."""
    n = int(dur * SR)
    if len(y) <= n:
        return y
    e = np.convolve(y ** 2, np.ones(n), "valid")[:: SR // 10]
    i = int(np.argmax(e)) * (SR // 10)
    return y[i:i + n]


def norm(y, peak=0.9):
    return y / (np.abs(y).max() + 1e-9) * peak


def fx(y, *effects):
    return sfx.sox(y, *effects)


def one_hit(y, i, ons, maxlen=0.45):
    end = ons[i + 1] if i + 1 < len(ons) else len(y)
    return trim(cut(y, ons[i], min(end, ons[i] + int(maxlen * SR))), 40)


def build():
    out = {}

    # --- knocks --------------------------------------------------------------------------------
    k5 = load(412856)                              # "Knocking five times", wooden door
    ons = hits(k5)
    best = max(range(len(ons)), key=lambda i: np.abs(k5[ons[i]:ons[i] + 2400]).max())
    knuckle = one_hit(k5, best, ons, 0.3)
    out["knock_guard"] = norm(fx(sfx.mix_at(1.4, [(0.0, knuckle, 1.0), (0.32, knuckle, 0.9), (0.64, knuckle, 1.0)]),
                                 "highpass", 80, "reverb", 25, 50, 60))
    heavy = load(592999)                           # "Heavy Knocking"
    h_ons = hits(heavy)
    knock = one_hit(heavy, 0, h_ons, 0.5)
    muffled = fx(knock, "lowpass", 900, "pitch", -150)          # heard through a closed door
    out["knock_inside"] = norm(fx(sfx.mix_at(3.2, [(0.0, muffled, 1.0), (0.9, muffled, 0.92), (1.8, muffled, 1.0)]),
                                  "reverb", 45, 50, 80))
    deep = fx(knock, "lowpass", 700, "pitch", -350)
    out["knock_final"] = norm(fx(sfx.mix_at(3.8, [(0.0, deep, 1.0), (1.1, deep, 0.95), (2.2, deep, 1.0)]),
                                 "reverb", 60, 50, 90))

    # --- footsteps (carpet: soften the hard-floor recording) -----------------------------------
    steps = load(415301)                           # "Indoor Footsteps"
    s_ons = hits(steps, min_gap=0.3)
    singles = [one_hit(steps, i, s_ons, 0.35) for i in range(min(len(s_ons), 8))]
    singles = sorted(singles, key=lambda s: -np.abs(s).max())[:4]
    carpet = [norm(fx(s, "lowpass", 2200, "highpass", 60), 0.7) for s in singles]
    out["step"], out["step2"] = carpet[0], carpet[1]
    out["step_heavy"] = norm(fx(singles[2], "lowpass", 1500, "pitch", -500, "reverb", 20), 0.9)

    # --- elevator ------------------------------------------------------------------------------
    out["ding"] = norm(fx(trim(load(459349)), "highpass", 300, "reverb", 30), 0.6)
    doors = load(439420)                            # "Elevator Approach and Doors Opening"
    out["elev_doors"] = norm(fx(loudest_window(doors[int(len(doors) * 0.55):], 2.6), "highpass", 60), 0.6)

    # --- tape machine, camera ------------------------------------------------------------------
    out["vcr"] = norm(sfx.mix_at(2.0, [(0.0, trim(load(623659)), 1.0), (0.9, trim(load(477684)), 0.7)]), 0.6)
    out["vcr_eject"] = norm(trim(load(154756)), 0.6)
    out["handle"] = norm(fx(trim(load(493338)), "lowpass", 5000), 0.35)
    out["drop"] = norm(sfx.mix_at(1.6, [(0.0, trim(load(483660), 25), 1.0)]), 0.8)
    out["drag"] = norm(fx(loudest_window(load(578493), 3.5), "lowpass", 2500, "reverb", 25), 0.7)
    out["button"] = norm(trim(load(560549)), 0.5)

    # --- beds (looped under scenes) ------------------------------------------------------------
    out["bed_fluoro"] = norm(fx(load(383657), "highpass", 70), 0.5)          # fluorescent tube hum
    out["bed_room"] = norm(fx(load(452222), "lowpass", 3000), 0.5)          # office ventilation
    out["bed_vhs"] = norm(load(531330), 0.5)                                  # VHS hum/crackle
    return out


if __name__ == "__main__":
    os.makedirs(sfx.OUT, exist_ok=True)
    for name, y in build().items():
        sfx.write(os.path.join(sfx.OUT, name + ".wav"), y)
        print(f"{name:13s} {len(y) / SR:5.2f}s")
