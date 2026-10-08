"""Voice pass 3. Run with the Chatterbox venv:  /home/user/tts/cb/bin/python film/voice3.py [ids...]

- one reference voice for every Dale line (out/tts_ref/dale.wav, a LibriTTS-R narrator), low exaggeration,
  so his voice and accent don't drift with emotion
- each take is checked by Whisper (words) and by pitch (no questioning lift on statements, no wild swings);
  up to TRIES takes, best one kept
- the yell is performed from a real shouted reference, then voice-converted into Dale
- door counts are recorded as one continuous take per tape and cut at the silences between numbers
- every line is loudness-levelled so it doesn't fade in and out
"""
import os, sys
import numpy as np
import torch, torchaudio as ta
import librosa, soundfile as sf
from num2words import num2words
from faster_whisper import WhisperModel
from chatterbox.tts import ChatterboxTTS
from chatterbox.vc import ChatterboxVC
import importlib, project
_s = importlib.import_module(project.SCRIPT)
VO, COUNTS, DELIVERY, LOUDNESS = _s.VO, _s.COUNTS, _s.DELIVERY, _s.LOUDNESS
from vo_common import ROOT, OUT, RAW, words, text_score, natural, stretch_words, finish

REF = os.path.join(ROOT, "out", "tts_ref")   # reference voices are shared
TRIES = int(os.environ.get("TRIES", 4))


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
            self.take(text, ref, ex, cfg, temp, 1000 * attempt + 17 + int(os.environ.get("VSEED", 0)), cand)
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
                p = os.path.join(RAW, f"{prefix}{n % 300:02d}.wav")
                sf.write(p, y[max(0, a - int(0.04 * sr)):b + int(0.08 * sr)], sr)
                h = self.heard(p)
                if str(n) not in h.replace(" ", "").replace("-", "") and text_score(num2words(n), h) < 0.6 \
                        and text_score(f"three {num2words(n % 300)}", h) < 0.6:
                    print(f"{name}: chunk for {n} heard as {h!r}, retrying", flush=True)
                    ok = False
                    break
            if ok:
                for n in numbers:
                    key = f"{prefix}{n % 300:02d}"
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
