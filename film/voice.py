"""Generate all voice lines with Piper, then give them a camcorder-mic / old-tape treatment with sox."""
import os, subprocess, sys
from script import VO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "vo")
VOICES = "/home/user/voices"
STYLE = {
    #          model                  length noise noise_w  sox effects
    "dale":   ("en_US-joe-medium",    1.08, 0.75, 0.85, "highpass 160 lowpass 5200 compand 0.02,0.2 -60,-60,-30,-15,0,-8 -3 reverb 12 30 40 gain -n -4"),
    "dale_q": ("en_US-joe-medium",    1.0,  0.9,  0.95, "highpass 180 lowpass 4800 compand 0.02,0.2 -60,-60,-30,-15,0,-8 -3 reverb 18 30 50 gain -n -9"),
    "dale_w": ("en_US-joe-medium",    0.95, 0.9,  1.0,  "highpass 250 lowpass 4200 tremolo 7 15 reverb 25 30 60 gain -n -13"),
    "memo":   ("en_US-lessac-medium", 1.22, 0.4,  0.5,  "pitch -300 highpass 300 lowpass 3200 overdrive 4 reverb 45 50 80 gain -n -5"),
}


def make(key, style, text):
    model, ls, ns, nw, fx = STYLE[style]
    raw = os.path.join(OUT, key + "_raw.wav")
    out = os.path.join(OUT, key + ".wav")
    if os.path.exists(out) and not os.environ.get("FORCE"):
        return
    subprocess.run([sys.executable, "-m", "piper", "-m", os.path.join(VOICES, model + ".onnx"), "-f", raw,
                    "--length-scale", str(ls), "--noise-scale", str(ns), "--noise-w-scale", str(nw)],
                   input=text.encode(), check=True, capture_output=True)
    subprocess.run(["sox", raw, "-r", "48000", "-c", "1", out, "gain", "-8", "pad", "0", "0.3"] + fx.split(), check=True)
    os.remove(raw)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for key, (style, text) in VO.items():
        make(key, style, text)
    print(len(VO), "lines")
