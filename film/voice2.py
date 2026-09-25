"""Voice every line with Chatterbox (expressive TTS), verify each take with Whisper, then give it the
camcorder-mic treatment. Needs the Chatterbox venv:  /home/user/tts/cb/bin/python film/voice2.py [ids...]
Reference voices come from film/voice_ref.py (Kokoro)."""
import difflib, os, re, subprocess, sys
import torch, torchaudio as ta
from num2words import num2words
from faster_whisper import WhisperModel
from chatterbox.tts import ChatterboxTTS
from script import VO, DELIVERY, EXAGGERATE
from voice import STYLE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "vo")
RAW = os.path.join(ROOT, "out", "vo_raw")
REF = os.path.join(ROOT, "out", "tts_ref")
TRIES = 5


def words(s):
    s = re.sub(r"\d+", lambda m: " " + num2words(int(m.group())) + " ", s.lower().replace("'", ""))
    w = [x for x in re.sub(r"[^a-z ]", " ", s).split() if x not in ("uh", "um", "er")]
    return [x for i, x in enumerate(w) if i == 0 or x != w[i - 1]]   # stutters: "I, I" == "I"


def score(expected, heard, key):
    if key.startswith("N"):  # "Three oh one" is heard as "301"
        n = 300 + int(key[1:])
        if str(n) in heard.replace(" ", "") or str(n)[1:] in heard:
            return 1.0
    return difflib.SequenceMatcher(None, words(expected), words(heard)).ratio()


def main():
    only = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RAW, exist_ok=True)
    tts = ChatterboxTTS.from_pretrained(device="cpu")
    asr = WhisperModel("small.en", device="cpu", compute_type="int8")
    report = []
    for key, (style, text) in VO.items():
        if only and key not in only:
            continue
        raw = os.path.join(RAW, key + ".wav")
        if os.path.exists(raw) and not only:
            continue
        ref, ex, cfg, temp = DELIVERY[style]
        ex = EXAGGERATE.get(key, ex)
        best = (-1, None, "")
        for attempt in range(TRIES):
            torch.manual_seed(1000 * attempt + hash(key) % 1000)
            wav = tts.generate(text.replace("...", "…"), audio_prompt_path=os.path.join(REF, ref + ".wav"),
                               exaggeration=ex, cfg_weight=cfg, temperature=temp)
            ta.save(raw, wav, tts.sr)
            heard = " ".join(s.text for s in asr.transcribe(raw, beam_size=3)[0]).strip()
            sc = score(text, heard, key)
            if sc > best[0]:
                best = (sc, wav.clone(), heard)
            if sc >= 0.9:
                break
        sc, wav, heard = best
        ta.save(raw, wav, tts.sr)
        fx = STYLE[style][4]
        subprocess.run(["sox", raw, "-r", "48000", "-c", "1", os.path.join(OUT, key + ".wav"),
                        "gain", "-8", "pad", "0.05", "0.3"] + fx.split(), check=True, capture_output=True)
        report.append((key, round(sc, 2), attempt + 1, heard))
        print(f"{key} score={sc:.2f} tries={attempt + 1} | {heard}", flush=True)
    bad = [r for r in report if r[1] < 0.9]
    print("done;", len(report), "lines,", len(bad), "below 0.9:", bad)


if __name__ == "__main__":
    main()
