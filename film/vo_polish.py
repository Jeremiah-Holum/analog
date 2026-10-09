"""Clean up generated voice takes before the camcorder treatment:
- trim the quiet junk at the start and end of a take
- shrink long dead stretches inside a line (Dia sometimes renders "..." or a laugh as 1-2 s of near-silence,
  which plays as the line cutting out); lines written with "..." keep a slightly longer pause
- level the speech inside the line, so it doesn't drop away halfway through
The untouched takes are kept in vo_raw_orig/ (first run only), then finish() re-renders vo/.
    FILM=item20 /home/user/tts/dia/bin/python film/vo_polish.py [ids...]"""
import os, shutil, sys
import numpy as np, librosa, soundfile as sf
import importlib, project
_s = importlib.import_module(project.SCRIPT)
from vo_common import RAW, finish

ORIG = os.path.join(project.OUT, "vo_raw_orig")
HOP = 0.01


def polish(y, sr, text):
    hop = int(HOP * sr)
    rms = librosa.feature.rms(y=y, frame_length=hop * 4, hop_length=hop, center=True)[0]
    db = 20 * np.log10(rms + 1e-7)
    speech = db > db.max() - 30
    idx = np.where(speech)[0]
    if len(idx) == 0:
        return y
    a, b = max(0, idx[0] - 6), min(len(db), idx[-1] + 10)              # trim, keep a little air
    keep_gap = 0.55 if "..." in text or "…" in text else 0.4
    pieces, gap_start, i = [], None, a
    cur = a
    for i in range(a, b):
        if not speech[i]:
            gap_start = i if gap_start is None else gap_start
        else:
            if gap_start is not None and (i - gap_start) * HOP > keep_gap:   # shrink this dead stretch
                cut_from = gap_start + int(keep_gap / 2 / HOP)
                cut_to = i - int(keep_gap / 2 / HOP)
                pieces.append(y[cur * hop:cut_from * hop])
                cur = cut_to
            gap_start = None
    pieces.append(y[cur * hop:b * hop])
    fade = int(0.012 * sr)
    out = pieces[0]
    for p in pieces[1:]:                                                    # short crossfades at each cut
        if len(out) > fade and len(p) > fade:
            out = np.concatenate([out[:-fade], out[-fade:] * np.linspace(1, 0, fade) + p[:fade] * np.linspace(0, 1, fade), p[fade:]])
        else:
            out = np.concatenate([out, p])
    # level: a slow gain that lifts quiet speech (max +12 dB) and tames peaks (max -6 dB); noise is left alone
    rms = librosa.feature.rms(y=out, frame_length=hop * 4, hop_length=hop, center=True)[0]
    db = 20 * np.log10(rms + 1e-7)
    ref = np.percentile(db[db > db.max() - 30], 70)
    gain_db = np.where(db > db.max() - 32, np.clip(ref - db, -6, 12), 0.0)
    k = 25
    gain_db = np.convolve(gain_db, np.ones(k) / k, "same")
    g = np.interp(np.arange(len(out)), np.arange(len(gain_db)) * hop, 10 ** (gain_db / 20))
    out = out * g
    return out / max(1e-6, np.abs(out).max()) * 0.9


def main():
    only = sys.argv[1:]
    os.makedirs(ORIG, exist_ok=True)
    dia = getattr(_s, "DIA", {})
    for key, (style, text) in _s.VO.items():
        if only and key not in only:
            continue
        raw = os.path.join(RAW, key + ".wav")
        if not os.path.exists(raw):
            continue
        orig = os.path.join(ORIG, key + ".wav")
        if not os.path.exists(orig):
            shutil.copy(raw, orig)
        y, sr = librosa.load(orig, sr=None)
        z = polish(y, sr, dia.get(key, text))
        sf.write(raw, z, sr)
        finish(raw, key, style)
        print(f"{key}: {len(y) / sr:.1f}s -> {len(z) / sr:.1f}s", flush=True)


if __name__ == "__main__":
    main()
