"""Reference voices for Chatterbox. Run with the Kokoro venv:
/home/user/tts/kk/bin/python film/voice_ref.py  (model files in /home/user/tts)

Dale's references are real acted speech from one actor (RAVDESS, Actor 21, CC BY-NC-SA 4.0,
https://zenodo.org/records/1188976) - calm, scared and yelling - so his voice keeps human texture.
The memo voice is Kokoro (bm_george)."""
import glob, os, subprocess
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "out", "tts_ref")
k = Kokoro("/home/user/tts/kokoro-v1.0.onnx", "/home/user/tts/voices-v1.0.bin")
os.makedirs(REF, exist_ok=True)
RAV = "/home/user/tts/ravdess/Actor_21"
# RAVDESS names: 03-01-<emotion>-<intensity>-<statement>-<rep>-21.wav
DALE = {
    "dale_calm": ["01-01", "02-01", "02-02"],       # neutral, calm (normal + strong)
    "dale_scared": ["06-01", "06-02", "04-02"],     # fearful normal/strong, sad strong
    "dale_yell": ["05-02", "06-02"],                # angry strong, fearful strong: real shouting
}
for name, codes in DALE.items():
    files = [f for c in codes for f in sorted(glob.glob(f"{RAV}/03-01-{c}-*.wav"))]
    parts = []
    for i, f in enumerate(files):  # trim silence from each clip, then join with short gaps
        t = os.path.join(REF, f"_part{i}.wav")
        subprocess.run(["sox", f, "-r", "24000", "-c", "1", t, "silence", "1", "0.05", "1%", "reverse",
                        "silence", "1", "0.05", "1%", "reverse", "pad", "0", "0.25"], check=True)
        parts.append(t)
    subprocess.run(["sox", *parts, os.path.join(REF, name + ".wav"), "norm", "-3"], check=True)
    for t in parts:
        os.remove(t)

for name, voice, lang, speed, text in [
    ("dale_kokoro", "am_michael", "en-us", 0.95, "Okay, so this is the third floor. Every night around two the lights start going out, "
     "and maintenance keeps telling me nothing is wrong. I've worked nights here for six years and I've never seen anything like it."),
    ("memo", "bm_george", "en-gb", 0.9, "Notice to all staff. The following procedures are effective immediately and apply to every "
     "employee and contractor in this building. Compliance is mandatory. Thank you for your cooperation."),
]:
    a, sr = k.create(text, voice=voice, speed=speed, lang=lang)
    sf.write(os.path.join(REF, name + ".wav"), a, sr)
