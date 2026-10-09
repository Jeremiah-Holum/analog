"""Audition Dia voices: one line, several seeds, no voice prompt (every seed is a different person).
    /home/user/tts/dia/bin/python film/dia_audition.py OUT_DIR "line text" SEED [SEED ...]
For each take prints the median pitch (to tell e.g. an older woman from a man) and what Whisper heard.
The take you pick becomes that character's voice prompt (with the line as its transcript)."""
import os, sys
import numpy as np, torch, librosa
from faster_whisper import WhisperModel
from transformers import AutoProcessor, DiaForConditionalGeneration

CK = "nari-labs/Dia-1.6B-0626"
out_dir, text, seeds = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
os.makedirs(out_dir, exist_ok=True)
proc = AutoProcessor.from_pretrained(CK)
DEVICE = os.environ.get("DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
model = DiaForConditionalGeneration.from_pretrained(CK, torch_dtype=torch.float32).to(DEVICE)
asr = WhisperModel("small.en", device="cpu", compute_type="int8")
for seed in seeds:
    torch.manual_seed(seed)
    inp = proc(text=[f"[S1] {text}"], padding=True, return_tensors="pt").to(DEVICE)
    out = model.generate(**inp, max_new_tokens=1600, guidance_scale=3.0, temperature=1.8, top_p=0.90, top_k=45)
    path = os.path.join(out_dir, f"seed{seed}.wav")
    proc.save_audio(proc.batch_decode(out.cpu()), path)
    y, sr = librosa.load(path, sr=16000)
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr)
    pitch = float(np.nanmedian(f0[voiced])) if voiced.any() else 0.0
    heard = " ".join(s.text for s in asr.transcribe(path, beam_size=3)[0]).strip()
    print(f"seed={seed} pitch={pitch:.0f}Hz dur={len(y) / sr:.1f}s | {heard}", flush=True)
