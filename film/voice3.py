"""Voice pass 3. Run with the Chatterbox venv:  /home/user/tts/cb/bin/python film/voice3.py [ids...]

- one reference voice for every Dale line (out/tts_ref/dale.wav, a LibriTTS-R narrator), low exaggeration,
  so his voice and accent don't drift with emotion
- each take is checked by Whisper (words) and by pitch (no questioning lift on statements, no wild swings);
  up to TRIES takes, best one kept
- the yell is performed from a real shouted reference, then voice-converted into Dale
- door counts are recorded as one continuous take per tape and cut at the silences between numbers
- every line is loudness-levelled so it doesn't fade in and out
"""
import difflib, os, re, subprocess, sys
import numpy as np
import torch, torchaudio as ta
import librosa, soundfile as sf
from num2words import num2words
from faster_whisper import WhisperModel
from chatterbox.tts import ChatterboxTTS
from chatterbox.vc import ChatterboxVC
from script import VO, COUNTS, DELIVERY, LOUDNESS
from voice import STYLE
from prosody import measure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "vo")
RAW = os.path.join(ROOT, "out", "vo_raw")
REF = os.path.join(ROOT, "out", "tts_ref")
TRIES = 4


def words(s):
    s = re.sub(r"\d+", lambda m: " " + num2words(int(m.group())) + " ", s.lower().replace("'", ""))
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


class Voicer:
    def __init__(self):
        self.tts = ChatterboxTTS.from_pretrained(device="cpu")
        self.vc = None
        self.asr = WhisperModel("small.en", device="cpu", compute_type="int8")

    def heard(self, path):
        return " ".join(s.text for s in self.asr.transcribe(path, beam_size=3)[0]).strip()

    def take(self, text, ref, ex, cfg, temp, seed, path):
        torch.manual_seed(seed)
        wav = self.tts.generate(text.replace("...", "…"), audio_prompt_path=os.path.join(REF, ref + ".wav"),
                                exaggeration=ex, cfg_weight=cfg, temperature=temp)
        ta.save(path, wav, self.tts.sr)

    def to_dale(self, path):
        if self.vc is None:
            self.vc = ChatterboxVC.from_pretrained(device="cpu")
        wav = self.vc.generate(path, target_voice_path=os.path.join(REF, "dale.wav"))
        ta.save(path, wav, self.vc.sr)

    def line(self, key, style, text):
        marked = [re.sub(r"[^a-z']", "", w.lower()) for w in text.split() if "~" in w]
        text = text.replace("~", "")
        ref, ex, cfg, temp = DELIVERY[style]
        raw = os.path.join(RAW, key + ".wav")
        best = None
        for attempt in range(TRIES):
            cand = os.path.join(RAW, f"{key}_try{attempt}.wav")
            self.take(text, ref, ex, cfg, temp, 1000 * attempt + 17, cand)
            if style == "dale_yell":
                self.to_dale(cand)
            heard = self.heard(cand)
            ts = text_score(text, heard)
            pen, m = natural(cand, text, style)
            total = (1 - ts) * 5 + pen
            if best is None or total < best[0]:
                best = (total, cand, heard, ts, pen)
            if ts >= 0.9 and pen < 0.3:
                break
        total, cand, heard, ts, pen = best
        os.replace(cand, raw)
        if marked:
            stretch_words(raw, marked, self.asr)
        for a in range(TRIES):
            p = os.path.join(RAW, f"{key}_try{a}.wav")
            if os.path.exists(p):
                os.remove(p)
        finish(raw, key, style)
        print(f"{key} words={ts:.2f} prosody_penalty={pen:.2f} tries={attempt + 1} | {heard}", flush=True)
        return ts, pen

    def count(self, name, spec):
        """One continuous counting take, cut at the silences between numbers."""
        style, prefix, numbers, text = spec
        ref, ex, cfg, temp = DELIVERY[style]
        for attempt in range(TRIES + 2):
            path = os.path.join(RAW, f"{name}.wav")
            self.take(text, ref, ex, cfg, temp, 500 + attempt, path)
            y, sr = librosa.load(path, sr=None)
            iv = librosa.effects.split(y, top_db=32, frame_length=1024, hop_length=256)
            while len(iv) > len(numbers):                      # merge the closest pair of chunks
                gaps = [iv[i + 1][0] - iv[i][1] for i in range(len(iv) - 1)]
                i = int(np.argmin(gaps))
                iv = np.vstack([iv[:i], [[iv[i][0], iv[i + 1][1]]], iv[i + 2:]])
            if len(iv) != len(numbers):
                print(f"{name}: {len(iv)} chunks for {len(numbers)} numbers, retrying", flush=True)
                continue
            ok = True
            for (a, b), n in zip(iv, numbers):
                p = os.path.join(RAW, f"{prefix}{n - 300:02d}.wav")
                sf.write(p, y[max(0, a - int(0.04 * sr)):b + int(0.08 * sr)], sr)
                h = self.heard(p)
                if str(n) not in h.replace(" ", "").replace("-", "") and text_score(num2words(n), h) < 0.6 \
                        and text_score(f"three {num2words(n - 300)}", h) < 0.6:
                    print(f"{name}: chunk for {n} heard as {h!r}, retrying", flush=True)
                    ok = False
                    break
            if ok:
                for n in numbers:
                    key = f"{prefix}{n - 300:02d}"
                    finish(os.path.join(RAW, key + ".wav"), key, style)
                print(f"{name} ok, tries={attempt + 1}", flush=True)
                return True
        print(f"{name} FAILED", flush=True)
        return False


def main():
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    v = Voicer()
    for name, spec in COUNTS.items():
        if not only or name in only:
            v.count(name, spec)
    for key, (style, text) in VO.items():
        if only and key not in only:
            continue
        if style == "memo":   # keep the memo takes, just level them
            raw = os.path.join(RAW, key + ".wav")
            if os.path.exists(raw):
                finish(raw, key, style)
            continue
        v.line(key, style, text)
    print("done")


if __name__ == "__main__":
    main()
