"""Speaker similarity to a reference voice, using Chatterbox's speaker encoder. Run in the Chatterbox venv:
    /home/user/tts/cb/bin/python film/spk_sim.py ref.wav take1.wav take2.wav ...
Prints one cosine similarity per take. Calibration on Gary (3 s clips): the same voice ~0.95,
a different Dia voice ~0.70."""
import sys
import numpy as np, librosa, torch
from huggingface_hub import hf_hub_download
from chatterbox.models.voice_encoder import VoiceEncoder

ve = VoiceEncoder()
ve.load_state_dict(torch.load(hf_hub_download("ResembleAI/chatterbox", "ve.pt"), map_location="cpu"))
ve.eval()


def emb(p):
    y, _ = librosa.load(p, sr=16000)
    e = ve.embeds_from_wavs([y], sample_rate=16000)[0]
    return e / np.linalg.norm(e)


ref = emb(sys.argv[1])
for p in sys.argv[2:]:
    print(f"{float(np.dot(ref, emb(p))):.3f}", flush=True)
