"""Voice pass 4: Dia-1.6B (Nari Labs). Run with the Dia venv:
    FILM=item15 /home/user/tts/dia/bin/python film/voice_dia.py [ids...]

- every line continues from one take picked by ear (script.DIA_PROMPT: audio + its exact transcript,
  or script.DIA_PROMPTS: one per style, for films with several voices), so each voice stays the same person
- nonverbal cues in the text, e.g. (laughs), (clears throat), are performed by the model
- each take is checked by Whisper (words) and by a speaker encoder (is it still the same man?);
  up to TRIES takes, best one kept
- same camcorder treatment and loudness levelling as voice3.py
"""
import os, re, subprocess, sys, time
import numpy as np
import torch, librosa, soundfile as sf
from faster_whisper import WhisperModel
from transformers import AutoProcessor, DiaForConditionalGeneration
import importlib, project
_s = importlib.import_module(project.SCRIPT)
from vo_common import ROOT, OUT, RAW, text_score, finish, words

CK = "nari-labs/Dia-1.6B-0626"
TRIES = int(os.environ.get("TRIES", 4))
TEMP = float(os.environ.get("TEMP", 1.8))
SR = 44100
CB_PY = "/home/user/tts/cb/bin/python"      # the speaker encoder lives in the Chatterbox venv
SIM_OK = 0.82                                # 3 s clips: same voice ~0.95, another Dia voice ~0.70
SIM_SHORT = 0.75                             # 1.2 s clips: same voice ~0.85, another Dia voice ~0.62
DEVICE = os.environ.get("DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
CB_PY = os.environ.get("CB_PY", CB_PY)


def spoken(text):
    """The words Whisper should hear: no (cues), no ~ marks."""
    return re.sub(r"\([^)]*\)", " ", text).replace("~", "")


class Voicer:
    def __init__(self):
        self.proc = AutoProcessor.from_pretrained(CK)
        self.model = DiaForConditionalGeneration.from_pretrained(CK, torch_dtype=torch.float32).to(DEVICE)
        self.asr = WhisperModel("small.en", device="cpu", compute_type="int8")   # small and fast enough on the CPU
        print("device:", DEVICE, flush=True)
        self.cur = None

    def use(self, style):
        """Load the voice prompt for this style (paths with a / are relative to the repo, else out/tts_ref)."""
        spec = getattr(_s, "DIA_PROMPTS", {}).get(style) or _s.DIA_PROMPT
        if spec == self.cur:
            return
        wav, text = spec
        self.prompt_path = os.path.join(ROOT, wav) if "/" in wav else os.path.join(ROOT, "out", "tts_ref", wav)
        self.prompt, _ = librosa.load(self.prompt_path, sr=SR, mono=True)
        self.prompt_text = text
        self.cur = spec

    def sim(self, path):
        r = subprocess.run([CB_PY, os.path.join(ROOT, "film", "spk_sim.py"), self.prompt_path, path],
                           capture_output=True, text=True)
        return float(r.stdout.split()[-1]) if r.returncode == 0 and r.stdout.strip() else 0.8

    def convert(self, path):
        """Voice-convert a take onto the prompt voice, in place, if that keeps the words and improves the match."""
        out = path.replace(".wav", "_vc.wav")
        r = subprocess.run([CB_PY, os.path.join(ROOT, "film", "vc_to.py"), self.prompt_path, path, out],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            return None
        return out

    def heard(self, path):
        return " ".join(s.text for s in self.asr.transcribe(path, beam_size=3)[0]).strip()

    def take(self, text, seed, path):
        torch.manual_seed(seed)
        inp = self.proc(text=[f"[S1] {self.prompt_text} [S1] {text}"], audio=[self.prompt], padding=True,
                        return_tensors="pt").to(DEVICE)
        plen = self.proc.get_audio_prompt_len(inp["decoder_attention_mask"])
        n_words = len(spoken(text).split())
        budget = int((n_words * 0.5 + 2.5 + 1.2 * text.count("(")) * 86 * 1.6)   # ~86 frames per second
        out = self.model.generate(**inp, max_new_tokens=min(budget, 2400), guidance_scale=3.0,
                                  temperature=TEMP, top_p=0.90, top_k=45)
        self.proc.save_audio(self.proc.batch_decode(out.cpu(), audio_prompt_len=plen), path)
        y, sr = librosa.load(path, sr=None)
        y, _ = librosa.effects.trim(y, top_db=38)
        sf.write(path, y, sr)
        return len(y) / sr, n_words

    def group(self, name, keys, texts, style):
        """Short lines said as one longer take (the voice holds better, and the take is long enough to
        voice-convert), then cut where each line starts. Used for the door counts."""
        self.use(style)
        text = " ... ".join(texts)
        for attempt in range(TRIES + 2):
            cand = os.path.join(RAW, f"{name}_try.wav")
            t = time.time()
            self.take(text, 7 + 100 * attempt + int(os.environ.get("VSEED", 0)), cand)
            vc = self.convert(cand)
            if vc:
                os.replace(vc, cand)
            sim = self.sim(cand)
            y, sr = librosa.load(cand, sr=None)
            iv = self.cuts(cand, texts, len(y), sr)
            print(f"  {name} try{attempt} {time.time() - t:.0f}s voice={sim:.2f} pieces={len(iv)}", flush=True)
            if len(iv) != len(keys) or sim < SIM_OK - 0.06:
                continue
            whole = text_score(spoken(text), self.heard(cand))       # judge the take as a whole...
            ok, heard = whole >= 0.85, []
            for (a, b), key, tx in zip(iv, keys, texts):
                p = os.path.join(RAW, key + ".wav")
                piece, _ = librosa.effects.trim(y[a:b], top_db=38)
                sf.write(p, piece, sr)
                h = self.heard(p)
                heard.append(h)
                if text_score(spoken(tx), h) < 0.5:                   # ...and each piece only loosely (tiny clips mishear)
                    ok = False
            print(f"    whole={whole:.2f} heard: {' | '.join(heard)}", flush=True)
            if ok:
                for key in keys:
                    finish(os.path.join(RAW, key + ".wav"), key, style)
                os.remove(cand)
                print(f"{name} ok voice={sim:.2f}", flush=True)
                return True
        print(f"{name} FAILED", flush=True)
        return False

    def cuts(self, path, texts, n, sr):
        """Split a grouped take where each line's first word starts (Whisper word timestamps)."""
        segs = self.asr.transcribe(path, beam_size=3, word_timestamps=True)[0]
        def head(word):     # first spoken word, with digits read out ("301" -> "three")
            ww = words(word)
            return ww[0] if ww else ""
        ws = [(head(w.word), w.start, w.end) for sg in segs for w in sg.words]
        first = head(spoken(texts[0]).split()[0])
        starts = [i for i, w in enumerate(ws) if w[0] == first]
        if len(starts) != len(texts):     # fall back to the biggest pauses (the lines are said with '...' between)
            y, _ = librosa.load(path, sr=sr)
            iv = librosa.effects.split(y, top_db=30, frame_length=1024, hop_length=256)
            if len(iv) < len(texts):
                return []
            gaps = sorted(range(len(iv) - 1), key=lambda i: iv[i + 1][0] - iv[i][1], reverse=True)[:len(texts) - 1]
            cut = sorted(int((iv[i][1] + iv[i + 1][0]) / 2) for i in gaps)
            bounds = [0] + cut + [n]
            return [(bounds[k], bounds[k + 1]) for k in range(len(texts))]
        # cut just before each line's first word (Whisper's word starts run a little late), not mid-gap
        bounds = [0] + [int(max(ws[i - 1][2], ws[i][1] - 0.15) * sr) for i in starts[1:]] + [n]
        return [(bounds[k], bounds[k + 1]) for k in range(len(texts))]

    def line(self, key, style, text):
        self.use(style)
        raw = os.path.join(RAW, key + ".wav")
        if key == getattr(_s, "DIA_USE_PROMPT", None):
            sf.write(raw, self.prompt, SR)
            finish(raw, key, style)
            print(f"{key} = the prompt take", flush=True)
            return
        best = None
        for attempt in range(TRIES):
            cand = os.path.join(RAW, f"{key}_try{attempt}.wav")
            t = time.time()
            dur, n_words = self.take(text, 2 + 100 * attempt + int(os.environ.get("VSEED", 0)), cand)
            heard = self.heard(cand)
            ts = text_score(spoken(text), heard)
            too_long = max(0.0, dur - (n_words * 0.6 + 2.5 + 1.5 * text.count("("))) * 0.2
            sim = self.sim(cand)
            weight = 10 if dur >= 2.5 else 8
            total = (1 - ts) * 5 + too_long + max(0.0, (0.88 if dur >= 2.5 else 0.82) - sim) * weight
            print(f"  {key} try{attempt} {time.time() - t:.0f}s dur={dur:.1f} words={ts:.2f} voice={sim:.2f} | {heard}",
                  flush=True)
            if best is None or total < best[0]:
                best = (total, cand, heard, ts, sim)
            if ts >= 0.9 and too_long == 0 and (sim >= SIM_OK or (dur < 2.5 and sim >= SIM_SHORT)
                                                or (dur >= 2.5 and attempt >= 1)):   # long ones can be converted
                break
        total, cand, heard, ts, sim = best
        dur = librosa.get_duration(path=cand)
        if sim < SIM_OK and dur >= 2.5:                         # the timbre drifted: convert it back onto Gary
            vc = self.convert(cand)
            if vc:
                vh, vts, vsim = self.heard(vc), None, self.sim(vc)
                vts = text_score(spoken(text), vh)
                print(f"  {key} converted: words={vts:.2f} voice={vsim:.2f} | {vh}", flush=True)
                if vts >= ts - 0.05 and vsim > sim:
                    os.replace(vc, cand)
                    heard, ts, sim = vh, vts, vsim
                elif os.path.exists(vc):
                    os.remove(vc)
        os.replace(cand, raw)
        for a in range(TRIES):
            p = os.path.join(RAW, f"{key}_try{a}.wav")
            if os.path.exists(p):
                os.remove(p)
        finish(raw, key, style)
        print(f"{key} words={ts:.2f} voice={sim:.2f} | {heard}", flush=True)


def main():
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    v = Voicer()
    dia = getattr(_s, "DIA", {})
    grouped = set()
    for name, keys in getattr(_s, "DIA_GROUPS", {}).items():
        grouped.update(keys)
        if not only or name in only:
            v.group(name, keys, [dia.get(k, _s.VO[k][1]) for k in keys], _s.VO[keys[0]][0])
    for key, (style, text) in _s.VO.items():
        if (only and key not in only) or style == "memo" or key in grouped:
            continue
        v.line(key, style, dia.get(key, text))
    print("done")


if __name__ == "__main__":
    main()
