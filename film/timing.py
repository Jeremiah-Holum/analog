"""Timing shared by the Blender shots and the edit (pure Python, no bpy)."""
FPS = 24


def count_walk(n_doors, y0, speed, look_ahead=1.3, first_plaque=4.02, spacing=1.6):
    """Times (s) at which the walking camera reads each door plaque."""
    return [(first_plaque + spacing * i - look_ahead - y0) / speed for i in range(n_doors)]


# door-counting walks: (n_doors, y0, speed, duration_s)
T1_COUNT = dict(n=9, y0=1.5, speed=0.63, dur=26.0)
T2_COUNT = dict(n=14, y0=1.5, speed=0.72, dur=36.0)

# frame lengths of the moving shots
SHOT_LEN = {
    "t1_elevator": int(14 * FPS),
    "t1_walk": int(20 * FPS),
    "t1_count": int(T1_COUNT["dur"] * FPS),
    "t2_count": int(T2_COUNT["dur"] * FPS),
    "t2_turn": int(4 * FPS),
    "t4_enter": int(16 * FPS),
    "t4_turn": int(4 * FPS),
}
