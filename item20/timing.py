"""ITEM 20 shot timing, shared by the Blender shots and the edit (pure Python)."""
FPS = 24
N_DOORS = 14
DENNY_COUNT = dict(n=N_DOORS, y0=1.5, dur=39.5, stop_y=24.4)
# When he reads each plaque (s into the count shot). Uneven like a real walk; he stalls at 310 and slows after.
COUNT_GAPS = [2.3, 2.5, 2.1, 2.4, 2.0, 2.6, 2.3, 2.8, 3.8, 3.1, 2.7, 3.0, 3.2]
GLANCE = [1.0, 0.8, 1.0, 0.55, 0.9, 0.6, 1.0, 0.75, 1.0, 1.0, 0.9, 1.0, 0.85, 1.0]   # how far he turns to each plaque


def count_times():
    ts = [1.7]
    for g in COUNT_GAPS:
        ts.append(ts[-1] + g)
    return ts


def plaque_y(i):
    return 4.02 + 1.6 * i


SHOT_LEN = {
    "n_open": 9 * FPS,
    "n_count": int(DENNY_COUNT["dur"] * FPS),
    "n_approach": 14 * FPS,
}
