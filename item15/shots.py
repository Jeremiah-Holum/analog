"""Shots for ITEM 15 ("SPACE AVAILABLE", March 1996). Reuses Film 1's kit and helpers.
Each builder sets up a scene and returns ("anim", n_frames) or ("still",)."""
import math, os, random
import bpy
import kit
import shots as s1                     # Film 1's shots: count walk, desk, office props, helpers
from kit import key_cam, look
from timing import FPS, count_walk

ROOT = s1.ROOT
TEX = s1.TEX

GARY_COUNT = dict(n=12, y0=1.5, speed=0.7, dur=34.0, stop_y=24.6)
SHOT_LEN = {
    "g_open2": 20 * FPS,
    "g_open3": 8 * FPS,
    "g_count": int(GARY_COUNT["dur"] * FPS),
    "g_enter": 12 * FPS,
    "g_turn": 7 * FPS,
    "g_close": 4 * FPS,
}


def hall12(M, modes=None, **kw):
    """The third floor as Gary finds it: twelve doors, lights working (it's daytime)."""
    modes = modes or ["ok", "ok", "ok", "bad", "ok", "ok", "ok", "bad", "dying", "dying"]
    return kit.hallway(M, 12, modes=modes, tail=5.0, seed=9, **kw)


def daylight(fixtures):
    s1.static_levels(fixtures)


# ------------------------------------------------------------------ lobby
def lobby():
    """Dale's old desk, daytime. One monitor still shows the third floor, end door open."""
    s1.desk("B")()
    for l in bpy.data.lights:
        if l.name.startswith("fl"):
            l.energy = 55
    for m in bpy.data.materials:
        if m.name.startswith("tube"):
            for n in m.node_tree.nodes:
                if n.type == 'EMISSION':
                    n.inputs["Strength"].default_value = 6.0
    look(bpy.context.scene.camera, (0.45, -1.15, 1.6), (-0.15, 1.2, 0.95))
    return ("still",)


# ------------------------------------------------------------------ elevator
def elevator_panel():
    """Close-up of the car's button panel: 3 is taped over."""
    kit.reset(61); M = kit.Mats()
    kit.elevator(M)
    kit.box("floor", (0, 0, -0.05), (6, 6, 0.1), M.carpet)
    x = 0.795
    kit.box("panel", (x, -0.45, 1.2), (0.012, 0.24, 0.62), M.steel)
    lit, _ = kit.mat_emit("btn_lit", (1.0, 0.75, 0.3), 3)
    tape = kit.mat_flat("tape", (0.72, 0.68, 0.55), 0.8)
    marker = kit.mat_flat("marker", (0.05, 0.05, 0.08), 0.6)
    for i, n in enumerate((1, 2, 3, 4)):
        z = 0.98 + i * 0.13
        kit.cyl(f"btn{n}", (x - 0.012, -0.47, z), 0.028, 0.012, lit if n == 2 else M.grey, rot=(0, math.pi / 2, 0))
        kit.text(str(n), (x - 0.01, -0.39, z), (math.pi / 2, 0, -math.pi / 2), 0.045, M.white)
    kit.box("tape", (x - 0.022, -0.45, 1.24), (0.004, 0.2, 0.07), tape, rot=(0.06, 0, 0))
    kit.text("OUT OF SERVICE", (x - 0.026, -0.45, 1.24), (math.pi / 2 + 0.06, 0, -math.pi / 2), 0.022, marker)
    cam = kit.camera(30)
    look(cam, (0.38, -0.55, 1.32), (x, -0.45, 1.18))
    return ("still",)


def open_on(floor):
    """Doors open from inside the car onto the 2nd floor office or the 3rd floor hallway."""
    def build():
        sc = kit.reset(62 if floor == 2 else 63); M = kit.Mats()
        dl, dr = kit.elevator(M)
        n = SHOT_LEN["g_open2" if floor == 2 else "g_open3"]
        s1.set_frames(sc, n)
        for f, xl in ((1, -0.25), (20, -0.25), (70, -0.74)):
            dl.location.x, dr.location.x = xl, -xl
            dl.keyframe_insert("location", frame=f); dr.keyframe_insert("location", frame=f)
        cam = kit.camera()
        if floor == 2:
            kit.office(M, (0, 0.0, 0))
            fx = []
            for x in (-2.0, 0.0, 2.0):
                for y in (1.5, 4.0, 6.5, 8.6):
                    dead = x < 0 and y > 6               # the far-left corner is dark
                    f = kit.Fixture(y, x=x, power=70, mode="dead" if dead else "ok")
                    fx.append(f)
            s1.animate_all(fx, n)
            kit.figure((-3.35, 8.35, 0), toward=(0.5, 2.0), head_tilt=0.2)
            key_cam(cam, 1, (0.05, -1.25, 1.58), (0, 8, 1.35))
            key_cam(cam, 75, (0.05, -1.2, 1.58), (0, 8, 1.4))
            key_cam(cam, 190, (0.2, 1.6, 1.6), (0.5, 8, 1.35))
            key_cam(cam, 280, (0.3, 2.0, 1.6), (3.5, 6.5, 1.2))    # looks right
            key_cam(cam, 330, (0.3, 2.1, 1.6), (3.0, 7.5, 1.25))
            key_cam(cam, 420, (0.2, 2.2, 1.6), (-3.0, 8.8, 1.35))  # slow pan left, past the dark corner
            key_cam(cam, n, (0.1, 2.3, 1.6), (-3.8, 6.0, 1.3))
            kit.handheld(cam, 0.9, walking=True)
        else:
            L, fx, _ = hall12(M)
            s1.animate_all(fx, n)
            kit.figure((0.2, L - 1.8, 0), toward=(0, 0))
            key_cam(cam, 1, (0.05, -1.25, 1.58), (0, 14, 1.35))
            key_cam(cam, n, (0.05, -1.15, 1.58), (0.1, 14, 1.4))
            kit.handheld(cam, 0.7)
        return ("anim", n)
    return build


# ------------------------------------------------------------------ the third floor
def g_count():
    """Gary counts twelve offices. The figure only moves while he's looking at a door, and it's gone after the last."""
    sc = kit.reset(64); M = kit.Mats()
    L, fx, _ = hall12(M)
    g = GARY_COUNT
    n = s1.count_shot(g["n"], g["y0"], g["speed"], g["dur"], sc, fx, stop_y=g["stop_y"])
    s1.animate_all(fx, n)
    fig = kit.figure((0.2, L - 1.8, 0), toward=(0, 0))
    times = count_walk(g["n"], g["y0"], g["speed"])
    y = L - 1.8
    fig.keyframe_insert("location", frame=1)
    for i, t in enumerate(times):
        f = int(round(t * FPS)) + 1
        cam_y = g["y0"] + g["speed"] * t
        if i >= 4:
            y = max(cam_y + 5.5, y - 2.3)
        fig.location.y = y
        fig.location.x = 0.25 * math.sin(i)
        fig.keyframe_insert("location", frame=f)
    for fc in fig.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT'
    gone = int(round(times[-1] * FPS)) + 2      # vanishes while he reads the last door
    for part in [fig] + list(fig.children_recursive):
        for f, hide in ((1, False), (gone - 1, False), (gone, True)):
            part.hide_render = hide
            part.keyframe_insert("hide_render", frame=f)
    return ("anim", n)


# ------------------------------------------------------------------ the corner office
def hall_office12(M):
    L, fx, end = hall12(M, end_open=1.45, void=False)
    kit.office(M, (0, L, 0))
    return L, fx


def g_enter():
    sc = kit.reset(65); M = kit.Mats()
    L, fx = hall_office12(M)
    s1.office_props(L)
    n = SHOT_LEN["g_enter"]; s1.set_frames(sc, n)
    cam = kit.camera()
    key_cam(cam, 1, (0.1, L - 1.6, 1.6), (0, L + 3, 1.2))
    key_cam(cam, 100, (0.05, L + 0.4, 1.6), (-1.5, L + 4.5, 1.1))
    key_cam(cam, 190, (0.5, L + 2.4, 1.58), (0.8, L + 7, 1.1))
    key_cam(cam, n, (1.0, L + 4.9, 1.55), (2.0, L + 6.9, 1.0))
    kit.handheld(cam, 1.0, walking=True)
    s1.animate_all(fx, n)
    return ("anim", n)


def g_tv():
    kit.reset(66); M = kit.Mats()
    L, fx = hall_office12(M)
    s1.office_props(L, screen="tv_feed")
    daylight(fx)
    cam = kit.camera(26)
    look(cam, (1.85, L + 5.85, 1.22), (2.0, L + 6.64, 1.0))
    return ("still",)


def g_turn():
    """He turns around. The doorway is empty."""
    sc = kit.reset(67); M = kit.Mats()
    L, fx = hall_office12(M)
    s1.office_props(L)
    n = SHOT_LEN["g_turn"]; s1.set_frames(sc, n)
    cam = kit.camera()
    key_cam(cam, 1, (1.85, L + 5.85, 1.22), (2.0, L + 6.64, 1.0))
    key_cam(cam, 6, (1.84, L + 5.85, 1.22), (1.9, L + 6.64, 1.05))
    key_cam(cam, 24, (1.75, L + 5.8, 1.35), (0.0, L + 0.5, 1.4))
    key_cam(cam, n, (1.7, L + 5.75, 1.35), (0.0, L + 0.5, 1.35))
    kit.handheld(cam, 1.1)
    s1.animate_all(fx, n)
    return ("anim", n)


# ------------------------------------------------------------------ sign-off
def g_close(with_doors=True):
    """Camera set down on the elevator handrail, looking out at the third floor. The doors close.
    Something is standing in the gap."""
    def build():
        sc = kit.reset(68); M = kit.Mats()
        L, fx, _ = hall12(M)
        dl, dr = kit.elevator(M)
        n = SHOT_LEN["g_close"]; s1.set_frames(sc, n)
        cam = kit.camera(20)
        look(cam, (0.35, -1.55, 0.95), (0.0, 6.0, 1.35), roll=0.07)
        if not with_doors:              # the long hold before the doors close
            for d, x in ((dl, -0.74), (dr, 0.74)):
                d.location.x = x
            daylight(fx)
            return ("still",)
        for f, xl in ((1, -0.74), (22, -0.74), (84, -0.25)):
            dl.location.x, dr.location.x = xl, -xl
            dl.keyframe_insert("location", frame=f); dr.keyframe_insert("location", frame=f)
        s1.animate_all(fx, n, {0: lambda f: 0.1 if 30 <= f < 34 else 1.0})
        fig = kit.figure((0.05, 1.9, 0), toward=(0.35, -1.55))
        for part in [fig] + list(fig.children_recursive):
            for f, hide in ((1, True), (32, True), (33, False)):
                part.hide_render = hide
                part.keyframe_insert("hide_render", frame=f)
        return ("anim", n)
    return build


STILLS = {
    "g_lobby": lobby,
    "g_panel": elevator_panel,
    "g_tv": g_tv,
    "g_hold": g_close(False),
}
ANIMS = {
    "g_open2": open_on(2),
    "g_open3": open_on(3),
    "g_count": g_count,
    "g_enter": g_enter,
    "g_turn": g_turn,
    "g_close": g_close(True),
}
ALL = {**STILLS, **ANIMS}
