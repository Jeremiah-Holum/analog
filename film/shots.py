"""Every shot in THE THIRD FLOOR. Each builder sets up a scene and returns ("anim", n_frames) or ("still",)."""
import math, os, random
import bpy
import kit
from kit import key_cam, look
from timing import SHOT_LEN, T1_COUNT, T2_COUNT, count_walk, FPS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "out", "tex")

T1_MODES = ["ok", "bad", "ok", "dying", "ok", "bad"]
T2_MODES = ["ok", "bad", "ok", "ok", "bad", "ok", "dying", "dead", "dead", "dying", "dead"]
T4_MODES = ["dying", "bad", "dying", "bad", "dying", "bad"]
LEVEL = {"ok": 1.0, "bad": 1.0, "dying": 0.3, "dead": 0.0}


def static_levels(fixtures, overrides=None):
    for i, f in enumerate(fixtures):
        lv = LEVEL[f.mode]
        if overrides and i in overrides:
            lv = overrides[i]
        f.set(lv)


def animate_all(fixtures, n, overrides=None):
    for i, f in enumerate(fixtures):
        f.animate(1, n, overrides.get(i) if overrides else None)


def locations_linear(cam):
    for fc in cam.animation_data.action.fcurves:
        if fc.data_path == "location":
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def set_frames(sc, n):
    sc.frame_start, sc.frame_end = 1, n


# ------------------------------------------------------------------ TAPE 1
def t1_elevator():
    sc = kit.reset(11); M = kit.Mats()
    L, fx, _ = kit.hallway(M, 9, modes=T1_MODES)
    dl, dr = kit.elevator(M)
    n = SHOT_LEN["t1_elevator"]; set_frames(sc, n)
    for f, xl in ((1, -0.25), (30, -0.25), (80, -0.74)):
        dl.location.x, dr.location.x = xl, -xl
        dl.keyframe_insert("location", frame=f); dr.keyframe_insert("location", frame=f)
    cam = kit.camera()
    key_cam(cam, 1, (0.05, -1.25, 1.58), (0, 12, 1.35))
    key_cam(cam, 170, (0.05, -1.2, 1.58), (0.1, 12, 1.4))
    key_cam(cam, n, (0.12, 2.3, 1.6), (0, 14, 1.35))
    kit.handheld(cam, 0.8, walking=True)
    animate_all(fx, n)
    return ("anim", n)


def t1_walk():
    sc = kit.reset(12); M = kit.Mats()
    L, fx, _ = kit.hallway(M, 9, modes=["ok", "ok", "bad", "dying", "bad", "ok"])
    n = SHOT_LEN["t1_walk"]; set_frames(sc, n)
    cam = kit.camera()
    y = lambda f: 2.3 + (8.4 - 2.3) * (f - 1) / (n - 1)
    key_cam(cam, 1, (0.12, y(1), 1.6), (0, 14, 1.35))
    key_cam(cam, 60, (0.1, y(60), 1.6), (0, 14, 1.5))
    key_cam(cam, 110, (0.05, y(110), 1.6), (0, 7.4, 2.6))     # looks up at the bad fixture
    key_cam(cam, 210, (0.05, y(210), 1.6), (0.1, 8.2, 2.55))
    key_cam(cam, 270, (0.1, y(270), 1.6), (0, 16, 1.4))
    key_cam(cam, n, (0.15, y(n), 1.6), (0, 18, 1.3))
    locations_linear(cam)
    kit.handheld(cam, 1.0, walking=True)
    animate_all(fx, n)
    return ("anim", n)


def count_shot(n_doors, y0, speed, dur, sc, fx, stop_y=None):
    n = int(dur * FPS); set_frames(sc, n)
    times = count_walk(n_doors, y0, speed)
    t_last = times[-1]
    stop_y = stop_y or (y0 + speed * t_last + 0.6)

    def ypos(t):
        if t <= t_last:
            return y0 + speed * t
        u = min(1.0, (t - t_last) / (dur - t_last))
        return y0 + speed * t_last + (stop_y - (y0 + speed * t_last)) * (1 - (1 - u) ** 2)

    cam = kit.camera()
    ahead = lambda t: (0, ypos(t) + 7, 1.35)
    pos = lambda t: (0.12 + 0.05 * math.sin(t * 0.7), ypos(t), 1.6)
    keys = [(0.0, "ahead")]
    for i, t in enumerate(times):
        keys += [(t - 0.8, "ahead"), (t - 0.1, i), (t + 0.45, i)]
    keys.append((times[-1] + 1.3, "ahead"))
    keys.append((dur, "far"))
    for t, what in keys:
        f = max(1, int(round(t * FPS)) + 1)
        if what == "ahead":
            tgt = ahead(t)
        elif what == "far":
            tgt = (0, ypos(t) + 12, 1.3)
        else:
            side = -1 if what % 2 == 0 else 1
            plaque_y = 4.02 + 1.6 * what
            tgt = (side * 1.1, plaque_y, 1.5)
        key_cam(cam, f, pos(t), tgt)
    for f in range(1, n + 1, 4):  # dense position keys keep the walking speed exact
        cam.location = pos((f - 1) / FPS)
        cam.keyframe_insert("location", frame=f)
    locations_linear(cam)
    kit.handheld(cam, 1.0, walking=True)
    return n


def t1_count():
    sc = kit.reset(13); M = kit.Mats()
    L, fx, _ = kit.hallway(M, 9, modes=T1_MODES)
    n = count_shot(T1_COUNT["n"], T1_COUNT["y0"], T1_COUNT["speed"], T1_COUNT["dur"], sc, fx)
    animate_all(fx, n)
    return ("anim", n)


def t1_end(level):
    def build():
        sc = kit.reset(14); M = kit.Mats()
        L, fx, _ = kit.hallway(M, 9, modes=T1_MODES)
        static_levels(fx, {5: level, 4: 1.0})
        cam = kit.camera()
        look(cam, (0.15, L - 2.1, 1.6), (0, L, 1.15))
        return ("still",)
    return build


# ------------------------------------------------------------------ TAPE 2
def hall14(M, **kw):
    return kit.hallway(M, 14, modes=T2_MODES, tail=9.0, seed=5, **kw)


def t2_start(variant):
    def build():
        sc = kit.reset(21); M = kit.Mats()
        L, fx, _ = hall14(M)
        kit.elevator(M)
        ov = {} if variant == "a" else {1: 0.05, 4: 0.0, 6: 0.0}
        static_levels(fx, ov)
        cam = kit.camera()
        look(cam, (0.1, 0.7, 1.6), (0, 22, 1.3))
        return ("still",)
    return build


def t2_count():
    sc = kit.reset(22); M = kit.Mats()
    L, fx, _ = hall14(M)
    n = count_shot(T2_COUNT["n"], T2_COUNT["y0"], T2_COUNT["speed"], T2_COUNT["dur"], sc, fx, stop_y=24.2)
    animate_all(fx, n)
    return ("anim", n)


def t2_figure(variant):
    def build():
        sc = kit.reset(23); M = kit.Mats()
        L, fx, _ = hall14(M)
        lv = {"A": 0.5, "B": 0.0, "C": 0.5}[variant]
        static_levels(fx, {10: lv * 1.3, 9: 0.0, 6: 0.25, 5: 0.8})
        if variant in "AB":
            kit.figure((0.2, L - 3.0, 0), toward=(0.15, 24.2), head_tilt=0.2)
        cam = kit.camera()
        look(cam, (0.15, 24.2, 1.6), (0, L - 2.4, 1.3))
        return ("still",)
    return build


def t2_turn():
    sc = kit.reset(24); M = kit.Mats()
    modes = list(T2_MODES); modes[6] = "bad"; modes[7] = "dead"
    L, fx, _ = kit.hallway(M, 14, modes=modes, tail=9.0, seed=5)
    n = SHOT_LEN["t2_turn"]; set_frames(sc, n)
    kit.figure((0.1, 21.7, 0), toward=(0.15, 24.2), reach=0.35, head_tilt=0.25)
    cam = kit.camera()
    key_cam(cam, 1, (0.15, 24.2, 1.6), (0, L - 2.4, 1.3))
    key_cam(cam, 4, (0.15, 24.2, 1.6), (0.3, L - 2.4, 1.3))
    key_cam(cam, 17, (0.1, 24.3, 1.58), (0.1, 15, 1.7))
    key_cam(cam, n, (0.1, 24.35, 1.57), (0.1, 15, 1.65))
    kit.handheld(cam, 1.6)
    animate_all(fx, n, {6: lambda f: 1.0 if f < 60 else None})
    return ("anim", n)


# ------------------------------------------------------------------ TAPE 3 (building cameras)
CCTV_POS = {
    "N": ((0.75, 0.6, 2.42), (-0.15, 19.4, 0.75)),
    "E": ((-0.95, 3.6, 2.45), (0.1, 1.2, 0.0)),
    "S": ((-0.95, 18.9, 2.45), (0, 2, 0.9)),
}


def cctv(cam_id, open_angle=0.0, fig=None, office=False, lens=None, cam_override=None, levels=None):
    def build():
        sc = kit.reset(31); M = kit.Mats()
        L, fx, _ = kit.hallway(M, 9, end_open=open_angle, void=not office,
                               modes=["ok", "ok", "ok", "bad", "ok", "ok"])
        kit.elevator(M)
        if office:
            kit.office(M, (0, L, 0))
        static_levels(fx, levels)
        pos, tgt = cam_override or CCTV_POS[cam_id]
        if fig:
            loc, kw = fig
            loc = (loc[0], loc[1] if loc[1] > 0 else L + loc[1], 0)
            kw.setdefault("toward", pos[:2])
            kit.figure(loc, **kw)
        cam = kit.camera(lens or {"N": 19}.get(cam_id, 14))
        look(cam, pos, tgt)
        return ("still",)
    return build


# ------------------------------------------------------------------ security desk
def desk(variant):
    def build():
        sc = kit.reset(41); M = kit.Mats()
        kit.box("floor", (0, 0, -0.05), (5, 5, 0.1), M.carpet)
        kit.box("ceiling", (0, 0, 2.65), (5, 5, 0.1), M.ceiling)
        kit.box("back", (0, 1.85, 1.3), (5, 0.1, 2.6), M.wall)
        kit.box("left", (-2.0, 0, 1.3), (0.1, 5, 2.6), M.wall)
        kit.box("right", (2.0, 0, 1.3), (0.1, 5, 2.6), M.wall)
        kit.box("desktop", (0, 1.05, 0.75), (2.4, 0.9, 0.05), M.desk)
        kit.box("desk_front", (0, 0.62, 0.38), (2.4, 0.04, 0.72), M.desk)
        feeds = ["cctv_N_open", "cctv_S", "cctv_E"] if variant == "B" else ["cctv_N", "cctv_S", "cctv_E"]
        for x, feed in zip((-0.68, 0.0, 0.68), feeds):
            kit.crt(M, (x, 1.2, 0.78), 0, os.path.join(TEX, feed + ".png"), 1.4)
        kit.box("phone", (0.95, 0.85, 0.81), (0.2, 0.22, 0.07), M.grey)
        kit.box("handset", (0.95, 0.85, 0.87), (0.06, 0.22, 0.05), M.grey)
        kit.cyl("mug", (-1.0, 0.8, 0.83), 0.045, 0.1, M.white)
        kit.box("logbook", (-0.35, 0.78, 0.785), (0.3, 0.22, 0.02), mat_logbook())
        kit.box("logpage", (-0.35, 0.78, 0.797), (0.28, 0.2, 0.004), M.paper)
        kit.cyl("pen", (-0.12, 0.76, 0.79), 0.005, 0.14, M.black, rot=(0, math.pi / 2, 0.3))
        # wall clock stopped at 2:00
        kit.cyl("clock", (1.2, 1.79, 1.95), 0.16, 0.03, M.white, rot=(math.pi / 2, 0, 0))
        kit.box("hour", (1.2, 1.765, 1.99), (0.012, 0.004, 0.09), M.black)
        kit.box("minute", (1.2, 1.765, 2.01), (0.008, 0.004, 0.13), M.black)
        kit.box("memo", (-1.3, 1.79, 1.6), (0.21, 0.004, 0.28), M.paper)
        fixture = kit.Fixture(0.6, power=45)
        fixture.set(1.0 if variant == "A" else 0.0)
        lamp = bpy.data.lights.new("lamp", 'POINT')
        lamp.energy, lamp.color, lamp.shadow_soft_size = 22, (1.0, 0.78, 0.5), 0.05
        lo = bpy.data.objects.new("lamp", lamp); lo.location = (-1.0, 1.1, 1.25)
        sc.collection.objects.link(lo)
        cam = kit.camera(24)
        look(cam, (0.1, -0.75, 1.3), (0, 1.25, 0.98))
        return ("still",)
    return build


def mat_logbook():
    return kit.mat_flat("logbook", (0.05, 0.12, 0.08), 0.6)


# ------------------------------------------------------------------ TAPE 4
def hall_office(M, open_angle=1.45):
    L, fx, end = kit.hallway(M, 9, end_open=open_angle, void=False, modes=T4_MODES, power=55)
    kit.office(M, (0, L, 0))
    return L, fx


def office_props(L, lamp_on=True, screen="tv_feed", screen_strength=1.8):
    lamp = bpy.data.lights.new("desklamp", 'POINT')
    lamp.energy, lamp.color, lamp.shadow_soft_size = (18 if lamp_on else 0), (1.0, 0.75, 0.45), 0.05
    lo = bpy.data.objects.new("desklamp", lamp); lo.location = (-2.0, L + 4.5, 1.15)
    bpy.context.scene.collection.objects.link(lo)
    M = kit.Mats()
    kit.cyl("shade", (-2.0, L + 4.5, 1.2), 0.1, 0.14, M.grey)
    kit.cyl("lampstem", (-2.0, L + 4.5, 0.95), 0.012, 0.4, M.steel)
    kit.crt(M, (2.0, L + 6.9, 0.76), 0, os.path.join(TEX, screen + ".png"), screen_strength)
    return lamp


def t4_door(level):
    def build():
        sc = kit.reset(51); M = kit.Mats()
        L, fx = hall_office(M)
        office_props(L)
        static_levels(fx, {5: level, 4: level * 0.5})
        cam = kit.camera()
        look(cam, (0.1, L - 3.2, 1.6), (0, L + 2, 1.1))
        return ("still",)
    return build


def t4_enter():
    sc = kit.reset(52); M = kit.Mats()
    L, fx = hall_office(M)
    office_props(L)
    n = SHOT_LEN["t4_enter"]; set_frames(sc, n)
    cam = kit.camera()
    key_cam(cam, 1, (0.1, L - 3.2, 1.6), (0, L + 2, 1.1))
    key_cam(cam, 150, (0.05, L - 0.4, 1.6), (0, L + 4, 1.2))
    key_cam(cam, 235, (0.25, L + 1.3, 1.6), (-2.0, L + 4.5, 1.0))
    key_cam(cam, 300, (0.5, L + 2.6, 1.58), (0.5, L + 7, 1.1))
    key_cam(cam, n, (1.0, L + 4.9, 1.55), (2.0, L + 6.9, 1.0))
    kit.handheld(cam, 1.1, walking=True)
    animate_all(fx, n)
    return ("anim", n)


def t4_tv(screen):
    def build():
        sc = kit.reset(53); M = kit.Mats()
        L, fx = hall_office(M)
        office_props(L, screen=screen)
        static_levels(fx)
        cam = kit.camera(26)
        look(cam, (1.85, L + 5.85, 1.22), (2.0, L + 6.64, 1.0))
        return ("still",)
    return build


FLOOR_CAM = lambda L: ((1.1, L + 5.6, 0.12), (0.0, L + 1.0, 0.35))


def t4_turn():
    sc = kit.reset(54); M = kit.Mats()
    L, fx = hall_office(M)
    lamp = office_props(L)
    n = SHOT_LEN["t4_turn"]; set_frames(sc, n)
    kit.figure((0.3, L + 1.6, 0), toward=(1.7, L + 5.8), reach=0.6, head_tilt=0.3)
    for f, e in ((1, 18), (38, 18), (40, 0), (43, 12), (45, 0)):
        lamp.energy = e
        lamp.keyframe_insert("energy", frame=f)
    cam = kit.camera()
    key_cam(cam, 1, (1.85, L + 5.85, 1.22), (2.0, L + 6.64, 1.0))
    key_cam(cam, 8, (1.83, L + 5.85, 1.22), (1.9, L + 6.64, 1.05))
    key_cam(cam, 22, (1.75, L + 5.8, 1.3), (0.3, L + 1.6, 2.1))
    key_cam(cam, 52, (1.72, L + 5.78, 1.28), (0.3, L + 1.6, 2.05))
    p, t = FLOOR_CAM(L)
    key_cam(cam, 62, (1.4, L + 5.65, 0.6), (0.2, L + 1.5, 0.6), roll=1.0)
    key_cam(cam, 68, p, t, roll=math.pi / 2)
    key_cam(cam, n, p, t, roll=math.pi / 2)
    kit.handheld(cam, 1.5)
    animate_all(fx, n)
    return ("anim", n)


def t4_floor(with_figure):
    def build():
        sc = kit.reset(55); M = kit.Mats()
        L, fx = hall_office(M)
        office_props(L, lamp_on=False, screen="tv_static", screen_strength=6.0)
        static_levels(fx, {i: 0.35 for i in range(6)})
        if with_figure:
            kit.figure((0.75, L + 4.3, 0), toward=(1.1, L + 5.6))
        cam = kit.camera()
        p, t = FLOOR_CAM(L)
        look(cam, p, t, roll=math.pi / 2)
        return ("still",)
    return build


# ------------------------------------------------------------------ registry
CCTV_STILLS = {
    "cctv_N": cctv("N"),
    "cctv_N_ajar": cctv("N", 0.35),
    "cctv_N_door": cctv("N", 1.3, ((0.0, -0.8), dict(head_tilt=0.2)), levels={5: 0.0}),
    "cctv_N_mid": cctv("N", 1.3, ((-0.3, 11.0), dict()), levels={3: 0.0}),
    "cctv_N_near": cctv("N", 1.3, ((0.35, 5.0), dict(reach=0.2)), levels={1: 0.0}),
    "cctv_N_open": cctv("N", 1.3),
    "cctv_E": cctv("E"),
    "cctv_E_face": cctv("E", 1.3, ((-0.25, 2.55), dict(head_tilt=0.3)), levels={0: 0.12, 1: 0.2}),
    "cctv_S": cctv("S"),
    "tv_feed_raw": cctv("F", 1.45, ((0.05, -0.8), dict(facing=0.0, toward=(0.05, 99))), office=True,
                        cam_override=((0.95, 14.0, 2.45), (0, 19.8, 1.1))),
}
STILLS = {
    "desk_A": desk("A"), "desk_B": desk("B"),
    "t1_end_lit": t1_end(1.0), "t1_end_dim": t1_end(0.12),
    "t2_start_a": t2_start("a"), "t2_start_b": t2_start("b"),
    "t2_fig_A": t2_figure("A"), "t2_fig_B": t2_figure("B"), "t2_fig_C": t2_figure("C"),
    "t4_door_a": t4_door(0.7), "t4_door_b": t4_door(0.12),
    "t4_tv_feed": t4_tv("tv_feed"), "t4_tv_static": t4_tv("tv_static"),
    "t4_floor_1": t4_floor(False), "t4_floor_2": t4_floor(True),
}
ANIMS = {
    "t1_elevator": t1_elevator, "t1_walk": t1_walk, "t1_count": t1_count,
    "t2_count": t2_count, "t2_turn": t2_turn,
    "t4_enter": t4_enter, "t4_turn": t4_turn,
}
ALL = {**CCTV_STILLS, **STILLS, **ANIMS}
