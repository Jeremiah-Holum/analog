"""Voice pass 4: Dia-1.6B (Nari Labs). Run with the Dia venv:
    FILM=item15 /home/user/tts/dia/bin/python film/voice_dia.py [ids...]

- every line continues from one take picked by ear (script.DIA_PROMPT: audio + its exact transcript),
  so the voice stays the same person from line to line
- nonverbal cues in the text, e.g. (laughs), (clears throat), are performed by the model
- each take is checked by Whisper; up to TRIES takes, best one kept
- same camcorder treatment and loudness levelling as voice3.py
"""
import os, re, sys, time
import numpy as np
import torch, librosa, soundfile as sf
from faster_whisper import WhisperModel
from transformers import AutoProcessor, DiaForConditionalGeneration
import importlib, project
_s = importlib.import_module(project.SCRIPT)
from vo_common import ROOT, OUT, RAW, text_score, finish

CK = "nari-labs/Dia-1.6B-0626"
TRIES = int(os.environ.get("TRIES", 3))
SR = 44100


def spoken(text):
    """The words Whisper should hear: no (cues), no ~ marks."""
    return re.sub(r"\([^)]*\)", " ", text).replace("~", "")


class Voicer:
    def __init__(self):
        self.proc = AutoProcessor.from_pretrained(CK)
        self.model = DiaForConditionalGeneration.from_pretrained(CK, torch_dtype=torch.float32)
        self.asr = WhisperModel("small.en", device="cpu", compute_type="int8")
        wav, text = _s.DIA_PROMPT
        self.prompt, _ = librosa.load(os.path.join(ROOT, "out", "tts_ref", wav), sr=SR, mono=True)
        self.prompt_text = text

    def heard(self, path):
        return " ".join(s.text for s in self.asr.transcribe(path, beam_size=3)[0]).strip()

    def take(self, text, seed, path):
        torch.manual_seed(seed)
        inp = self.proc(text=[f"[S1] {self.prompt_text} [S1] {text}"], audio=[self.prompt], padding=True,
                        return_tensors="pt")
        plen = self.proc.get_audio_prompt_len(inp["decoder_attention_mask"])
        n_words = len(spoken(text).split())
        budget = int((n_words * 0.5 + 2.5 + 1.2 * text.count("(")) * 86 * 1.6)   # ~86 frames per second
        out = self.model.generate(**inp, max_new_tokens=min(budget, 2400), guidance_scale=3.0,
                                  temperature=1.8, top_p=0.90, top_k=45)
        self.proc.save_audio(self.proc.batch_decode(out, audio_prompt_len=plen), path)
        y, sr = librosa.load(path, sr=None)
        y, _ = librosa.effects.trim(y, top_db=38)
        sf.write(path, y, sr)
        return len(y) / sr, n_words

    def line(self, key, style, text):
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
            total = (1 - ts) * 5 + too_long
            print(f"  {key} try{attempt} {time.time() - t:.0f}s dur={dur:.1f} words={ts:.2f} | {heard}", flush=True)
            if best is None or total < best[0]:
                best = (total, cand, heard, ts)
            if ts >= 0.9 and too_long == 0:
                break
        total, cand, heard, ts = best
        os.replace(cand, raw)
        for a in range(TRIES):
            p = os.path.join(RAW, f"{key}_try{a}.wav")
            if os.path.exists(p):
                os.remove(p)
        finish(raw, key, style)
        print(f"{key} words={ts:.2f} | {heard}", flush=True)


def main():
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    v = Voicer()
    dia = getattr(_s, "DIA", {})
    for key, (style, text) in _s.VO.items():
        if (only and key not in only) or style == "memo":
            continue
        v.line(key, style, dia.get(key, text))
    print("done")


if __name__ == "__main__":
    main()
