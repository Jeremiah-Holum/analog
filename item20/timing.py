"""ITEM 20 shot timing, shared by the Blender shots and the edit (pure Python)."""
FPS = 24
N_DOORS = 14
DENNY_COUNT = dict(n=N_DOORS, y0=1.5, speed=0.72, dur=38.0, stop_y=24.4)
SHOT_LEN = {
    "n_open": 9 * FPS,
    "n_count": int(DENNY_COUNT["dur"] * FPS),
    "n_approach": 14 * FPS,
}
