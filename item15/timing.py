"""ITEM 15 shot timing, shared by the Blender shots and the edit (pure Python)."""
FPS = 24
GARY_COUNT = dict(n=12, y0=1.5, speed=0.7, dur=34.0, stop_y=24.6)
SHOT_LEN = {
    "g_open2": 20 * FPS,
    "g_open3": 8 * FPS,
    "g_count": int(GARY_COUNT["dur"] * FPS),
    "g_enter": 12 * FPS,
    "g_turn": 7 * FPS,
    "g_close": 4 * FPS,
}
