"""Shots for ITEM 20 (COULEE AFTER DARK, live from the third floor, Oct. 31 1997).
Denny runs his own camera, a shoulder rig with a top light. Reuses Film 1's kit and helpers.
Each builder sets up a scene and returns ("anim", n_frames) or ("still",)."""
import math, random
import bpy
import kit
import shots as s1
from kit import key_cam, look
kit.REALISM = True
from timing import FPS, count_walk

ROOT = s1.ROOT
TEX = s1.TEX

from item20.timing import DENNY_COUNT, SHOT_LEN, N_DOORS, GLANCE, count_times, plaque_y

# Power's back on for the broadcast, mostly. Nine troffers down the hall.
MODES = ["ok", "dying", "bad", "dead", "ok", "dying", "dead", "bad", "dying"]


def hall14(M, modes=None, **kw):
    L, fx, end = kit.hallway(M, N_DOORS, modes=modes or MODES, tail=4.0, seed=20, **kw)
    kit.clutter_hall(M, L, seed=21)
    return L, fx, end


def cam_light(cam, energy=60.0):
    """The camera's top light: a warm, hard little spot riding on the camera."""
    d = bpy.data.lights.new("toplight", 'SPOT')
    d.energy, d.spot_size, d.spot_blend, d.shadow_soft_size = energy, math.radians(55), 0.6, 0.03
    d.color = (1.0, 0.86, 0.68)
    o = bpy.data.objects.new("toplight", d)
    bpy.context.scene.collection.objects.link(o)
    o.parent = cam
    o.location = (0.0, 0.12, 0.05)
    return d


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def add_bob(cam, f0, f1, amp=0.016):
    """Footsteps: a vertical bob at step rate and a slower side-to-side sway, eased in and out."""
    for fc in cam.animation_data.action.fcurves:
        if fc.data_path == "location" and fc.array_index in (0, 2):
            m = fc.modifiers.new('FNGENERATOR')
            m.function_type, m.use_additive = 'SIN', True
            hz = 1.8 if fc.array_index == 2 else 0.9
            m.amplitude = amp if fc.array_index == 2 else amp * 0.8
            m.phase_multiplier = 2 * math.pi * hz / FPS
            m.use_restricted_range = True
            m.frame_start, m.frame_end, m.blend_in, m.blend_out = f0, f1, 12, 12


def exit_glow(L, energy=2.5):
    """The EXIT sign over the end door is the only thing left when the power goes."""
    d = bpy.data.lights.new("exitglow", 'POINT')
    d.energy, d.color, d.shadow_soft_size = energy, (1.0, 0.08, 0.05), 0.15
    o = bpy.data.objects.new("exitglow", d)
    bpy.context.scene.collection.objects.link(o)
    o.location = (0, kit.HALL_W * 0 + L - 0.2, kit.HALL_H - 0.25)
    return d


# ------------------------------------------------------------------ 1:44 AM, the doors open on three
def n_open():
    sc = kit.reset(201); M = kit.Mats()
    L, fx, _ = hall14(M)
    dl, dr = kit.elevator(M)
    n = SHOT_LEN["n_open"]; s1.set_frames(sc, n)
    for f, xl in ((1, -0.25), (14, -0.25), (60, -0.74)):
        dl.location.x, dr.location.x = xl, -xl
        dl.keyframe_insert("location", frame=f); dr.keyframe_insert("location", frame=f)
    cam = kit.camera()
    cam_light(cam)
    key_cam(cam, 1, (0.05, -1.25, 1.62), (0, 14, 1.4))
    key_cam(cam, 80, (0.05, -1.1, 1.62), (0.1, 14, 1.42))
    key_cam(cam, n, (0.1, 0.9, 1.62), (0.2, 14, 1.35))
    kit.handheld(cam, 0.7)
    add_bob(cam, 80, n)
    s1.animate_all(fx, n)
    return ("anim", n)


# ------------------------------------------------------------------ 1:51 AM, Paul Voss calls
def n_hall(dim):
    """Standing just out of the elevator, looking down the hall while he takes the call. When the bad
    fixtures drop out, something is standing at the far end, in the dark. Barely."""
    def build():
        kit.reset(202); M = kit.Mats()
        L, fx, _ = hall14(M)
        kit.elevator(M)
        lv = {2: 0.0, 5: 0.05, 7: 0.0, 8: 0.0} if dim else {5: 0.3, 8: 0.25}
        s1.static_levels(fx, lv)
        if dim:
            kit.figure_real((0.3, L - 1.4, 0), toward=(0, 0), seed=3)
        cam = kit.camera(26)
        cam_light(cam)
        look(cam, (0.15, 0.9, 1.62), (0.05, 14, 1.42), roll=0.015)
        return ("still",)
    return build


# ------------------------------------------------------------------ 1:58 AM, the count
def n_count():
    """He walks and reads the plaques like a person: uneven pace, slowing at each one, eased glances (some only
    half a look), a stall at 310, footsteps in the camera."""
    sc = kit.reset(203); M = kit.Mats()
    L, fx, _ = hall14(M)
    g = DENNY_COUNT
    n = SHOT_LEN["n_count"]; s1.set_frames(sc, n)
    times = count_times()
    pts_t = [0.0] + times + [g["dur"]]
    pts_y = [g["y0"]] + [plaque_y(i) - 1.3 for i in range(len(times))] + [g["stop_y"]]

    def interp(t):
        for j in range(len(pts_t) - 1):
            if t <= pts_t[j + 1]:
                u = (t - pts_t[j]) / max(1e-6, pts_t[j + 1] - pts_t[j])
                return pts_y[j] + (pts_y[j + 1] - pts_y[j]) * u
        return pts_y[-1]
    y_lin = [interp(f / FPS) for f in range(n)]
    k = int(0.9 * FPS)                                               # smooth: he eases in and out of each read
    y = [sum(y_lin[min(n - 1, max(0, f + d))] for d in range(-k, k + 1)) / (2 * k + 1) for f in range(n)]
    cam = kit.camera()
    cam_light(cam)
    for f in range(1, n + 1, 2):
        t = (f - 1) / FPS
        yy = float(y[f - 1])
        ahead = (0.15 * math.sin(t * 0.3), yy + 7, 1.35 - 0.06 * math.sin(t * 0.5) - (0.1 if t > times[8] else 0.0))
        tgt, W = [0.0, 0.0, 0.0], 0.0
        for i, ti in enumerate(times):
            side = -1 if i % 2 == 0 else 1
            w = GLANCE[i] * (smooth((t - (ti - 0.75)) / 0.7) - smooth((t - (ti + 0.35)) / 0.9))
            if w > 0:
                p = (side * 1.1, plaque_y(i), 1.5)
                for c in range(3):
                    tgt[c] += w * p[c]
                W += w
        W = min(W, 1.0)
        tgt = [tgt[c] + (1 - W) * ahead[c] for c in range(3)] if W < 1 else tgt
        pos = (0.1 + 0.05 * math.sin(t * 0.7), yy, 1.6)
        key_cam(cam, f, pos, tuple(tgt))
    kit.handheld(cam, 0.6)
    add_bob(cam, 1, n, 0.017)
    s1.animate_all(fx, n)
    return ("anim", n)


# ------------------------------------------------------------------ 2:04 AM, Gary calls
def n_gary(dim):
    """Stopped past the fourteenth door, looking at the end of the hall: the corner office."""
    def build():
        kit.reset(204); M = kit.Mats()
        L, fx, _ = hall14(M)
        s1.static_levels(fx, {8: 0.0, 7: 0.15 if dim else 0.8, 6: 0.3 if dim else 1.0})
        cam = kit.camera(24)
        cam_light(cam)
        look(cam, (0.1, DENNY_COUNT["stop_y"], 1.62), (0.0, L + 2, 1.3), roll=-0.02)
        return ("still",)
    return build


# ------------------------------------------------------------------ 2:08 AM, the knocking
def n_approach():
    """He walks to the end door. The lights go out behind and ahead of him, one by one."""
    sc = kit.reset(205); M = kit.Mats()
    L, fx, _ = hall14(M)
    n = SHOT_LEN["n_approach"]; s1.set_frames(sc, n)
    cam = kit.camera()
    light = cam_light(cam)
    y0, y1 = DENNY_COUNT["stop_y"], L - 1.7
    key_cam(cam, 1, (0.1, y0, 1.62), (0.0, L + 2, 1.3))
    key_cam(cam, 40, (0.08, y0 + 0.3, 1.62), (0.0, L + 2, 1.35))
    key_cam(cam, n - 30, (0.05, y1, 1.6), (0.05, L + 1, 1.15))
    key_cam(cam, n, (0.05, y1 + 0.1, 1.6), (0.1, L + 1, 1.1))
    kit.handheld(cam, 0.8)
    add_bob(cam, 30, n - 20, 0.015)
    outs = {i: int(n * (0.25 + 0.08 * (8 - i))) for i in range(9)}       # far ones die first, then behind him
    s1.animate_all(fx, n, {i: (lambda f, i=i: 0.0 if f >= outs[i] else None) for i in range(9)})
    exit_glow(L)
    for f in range(1, n + 1):                                             # the top light starts to fail at the end
        e = 60.0
        if f > n - 40:
            e = 60.0 if random.random() > 0.35 else random.uniform(0, 20)
        light.energy = e
        light.keyframe_insert("energy", frame=f)
    return ("anim", n)


# ------------------------------------------------------------------ 2:10 AM, at the door
def n_door(variant):
    """At the corner office door. 'lit': his top light on the door. 'dark': the top light is gone, only the
    EXIT sign. 'dark_fig': same, and it is standing between him and the door, a silhouette against the red."""
    def build():
        kit.reset(206); M = kit.Mats()
        L, fx, _ = hall14(M, modes=["dead"] * 9)
        s1.static_levels(fx)
        cam = kit.camera(22)
        look(cam, (0.05, L - 3.4, 1.55), (0.05, L, 1.62), roll=0.03)
        if variant == "lit":
            cam_light(cam, 60.0)
        exit_glow(L, 2.5 if variant == "lit" else 4.0)
        if variant == "dark_fig":
            kit.figure_real((-0.1, L - 1.15, 0), toward=(0.05, L - 3.4), head_tilt=0.1, seed=11)
        return ("still",)
    return build


STILLS = {
    "n_hall_a": n_hall(False), "n_hall_b": n_hall(True),
    "n_gary_a": n_gary(False), "n_gary_b": n_gary(True),
    "n_door_lit": n_door("lit"), "n_door_dark": n_door("dark"), "n_door_fig": n_door("dark_fig"),
}
ANIMS = {
    "n_open": n_open,
    "n_count": n_count,
    "n_approach": n_approach,
}
ALL = {**STILLS, **ANIMS}
