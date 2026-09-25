"""Reference voices for Chatterbox, generated with Kokoro. Run with the Kokoro venv:
/home/user/tts/kk/bin/python film/voice_ref.py  (model files in /home/user/tts)"""
import os
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "out", "tts_ref")
k = Kokoro("/home/user/tts/kokoro-v1.0.onnx", "/home/user/tts/voices-v1.0.bin")
os.makedirs(REF, exist_ok=True)
for name, voice, lang, speed, text in [
    ("dale", "am_michael", "en-us", 0.95, "Okay, so this is the third floor. Every night around two the lights start going out, "
     "and maintenance keeps telling me nothing is wrong. I've worked nights here for six years and I've never seen anything like it."),
    ("memo", "bm_george", "en-gb", 0.9, "Notice to all staff. The following procedures are effective immediately and apply to every "
     "employee and contractor in this building. Compliance is mandatory. Thank you for your cooperation."),
]:
    a, sr = k.create(text, voice=voice, speed=speed, lang=lang)
    sf.write(os.path.join(REF, name + ".wav"), a, sr)
