"""Helpers shared by the voice generators (voice3.py: Chatterbox, voice_dia.py: Dia). No TTS imports here,
so it loads in either venv."""
import difflib, os, re, subprocess
import numpy as np
import librosa, soundfile as sf
from num2words import num2words
import importlib, project
_s = importlib.import_module(project.SCRIPT)
LOUDNESS = _s.LOUDNESS
from voice import STYLE
from prosody import measure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(project.OUT, "vo")
RAW = os.path.join(project.OUT, "vo_raw")


def say(digits):
    """Numbers the way people read them off a door or a phone: 301 -> three oh one, 310 -> three ten,
    0141 -> oh one four one; everything else as a plain number."""
    n = int(digits)
    if len(digits) == 3 and digits[0] != "0":
        rest = n % 100
        return f"{num2words(n // 100)} oh {num2words(rest)}" if rest < 10 else f"{num2words(n // 100)} {num2words(rest)}"
    if len(digits) >= 4 and digits[0] == "0":
        return " ".join("oh" if c == "0" else num2words(int(c)) for c in digits)
    if len(digits) == 4 and 1900 <= n < 2000:
        return num2words(n, to="year")
    return num2words(n)


def words(s):
    s = re.sub(r"\d+", lambda m: " " + say(m.group()) + " ", s.lower().replace("'", ""))
    s = re.sub(r"\ba+nd\b", "and", s)
    for a, b in (("dunno", "dont know"), ("gonna", "going to"), ("wanna", "want to"), ("em", "them"), ("all right", "alright"),
                 ("for", "four"), ("to", "two"), ("too", "two"), ("won", "one"), ("ate", "eight")):   # homophones
        s = re.sub(rf"\b{a}\b", b, s)
    w = [x for x in re.sub(r"[^a-z ]", " ", s).split() if x not in ("uh", "um", "er")]
    return [x for i, x in enumerate(w) if i == 0 or x != w[i - 1]]


def text_score(expected, heard):
    return difflib.SequenceMatcher(None, words(expected), words(heard)).ratio()


def natural(path, text, style):
    """Penalty for unnatural prosody (0 = fine)."""
    m = measure(path)
    p = 0.0
    if style != "dale_yell":
        p += max(0.0, m["range"] - 10.0) * 0.3            # sing-song pitch swings
        p += max(0.0, m["jump"] - 0.8) * 2.0
        if text.rstrip().endswith((".", "…", "...")):      # statements should fall at the end
            p += max(0.0, m["end_fall"] - 0.3) * 0.8
    return p, m


def stretch_words(path, marked, asr, factor=1.9):
    """Draw out the marked words ("be~" -> "beeee...") with a speech-quality time stretch of just that word."""
    y, sr = librosa.load(path, sr=None)
    segs = asr.transcribe(path, beam_size=3, word_timestamps=True)[0]
    ws = [(re.sub(r"[^a-z']", "", w.word.lower()), w.start, w.end) for sg in segs for w in sg.words]
    pieces, cur, i = [], 0, 0
    for target in marked:
        while i < len(ws) and ws[i][0] != target:
            i += 1
        if i == len(ws):
            print(f"    (couldn't find '{target}' to stretch)", flush=True)
            break
        a, b = int(ws[i][1] * sr), int(ws[i][2] * sr)
        tmp_in, tmp_out = path + ".w.wav", path + ".s.wav"
        sf.write(tmp_in, y[a:b], sr)
        subprocess.run(["sox", tmp_in, tmp_out, "tempo", "-s", f"{1 / factor:.3f}"], check=True, capture_output=True)
        word, _ = librosa.load(tmp_out, sr=sr)
        os.remove(tmp_in); os.remove(tmp_out)
        fade = min(int(0.01 * sr), len(word) // 4)
        word[:fade] *= np.linspace(0, 1, fade); word[-fade:] *= np.linspace(1, 0, fade)
        pieces += [y[cur:a], word]
        cur, i = b, i + 1
    pieces.append(y[cur:])
    sf.write(path, np.concatenate(pieces), sr)


def finish(raw, key, style):
    """Camcorder-mic treatment, then level to the style's loudness."""
    tmp = os.path.join(RAW, key + "_fx.wav")
    subprocess.run(["sox", raw, "-r", "48000", "-c", "1", tmp, "gain", "-8", "pad", "0.05", "0.3"]
                   + STYLE[style][4].split(), check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af",
                    f"loudnorm=I={LOUDNESS[style]}:LRA=4:TP=-2", "-ar", "48000", "-ac", "1",
                    os.path.join(OUT, key + ".wav")], check=True)
    os.remove(tmp)
