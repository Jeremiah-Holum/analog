"""Voice-convert takes onto a reference voice with ChatterboxVC (keeps the delivery, locks the timbre).
Run in the Chatterbox venv:  /home/user/tts/cb/bin/python film/vc_to.py ref.wav in.wav out.wav [in2.wav out2.wav ...]
Only used on takes of 2.5 s or more; very short clips come out garbled."""
import sys, torchaudio as ta
from chatterbox.vc import ChatterboxVC

vc = ChatterboxVC.from_pretrained(device="cpu")
ref, pairs = sys.argv[1], sys.argv[2:]
for src, dst in zip(pairs[::2], pairs[1::2]):
    ta.save(dst, vc.generate(src, target_voice_path=ref), vc.sr)
