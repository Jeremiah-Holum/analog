"""Pitch/loudness measurements used to reject unnatural TTS takes (needs librosa)."""
import numpy as np
import librosa


def measure(path):
    y, sr = librosa.load(path, sr=16000)
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=320, sr=sr, frame_length=1024, hop_length=160)
    st = 12 * np.log2(f0[voiced] / 100.0) if voiced.any() else np.array([0.0])
    n = len(st)
    if n < 10:
        return dict(jump=0, range=0, end_fall=0, loud_sd=0)
    jumps = np.abs(np.diff(st))
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=160)[0]
    db = 20 * np.log10(rms[rms > rms.max() * 0.1] + 1e-9)
    return dict(
        jump=float(np.percentile(jumps, 90)),                       # how sing-songy frame to frame
        range=float(np.percentile(st, 95) - np.percentile(st, 5)),  # overall pitch swing
        end_fall=float(np.median(st[int(n * 0.8):]) - np.median(st[int(n * 0.3):int(n * 0.7)])),  # + = rising end
        loud_sd=float(np.std(db)),                                  # volume wobble
    )
