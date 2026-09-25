# Scene-building kit for THE THIRD FLOOR. Imported by render.py inside Blender.
import bpy, math, random
from mathutils import Vector

RES = (384, 288)
FPS = 24
HALL_W = 2.2          # corridor width (x: -1.1 .. 1.1)
HALL_H = 2.6
DOOR_SPACING = 3.2


def reset(seed=1):
    random.seed(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    c = sc.cycles
    c.samples = 14
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.05
    c.use_denoising = False
    c.max_bounces = 4
    c.diffuse_bounces = 2
    c.glossy_bounces = 1
    c.transmission_bounces = 0
    c.transparent_max_bounces = 2
    c.caustics_reflective = c.caustics_refractive = False
    c.sample_clamp_indirect = 3
    c.filter_width = 1.8
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.fps = FPS
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.look = 'Medium High Contrast'
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0
    return sc


# ---------------------------------------------------------------- materials
def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes["Principled BSDF"]


def _coords(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs["Object"]


def _noise(nt, vec, scale, detail=6.0, rough=0.6):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def _ramp_mix(nt, fac, c1, c2, p1=0.4, p2=0.7):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position, r.color_ramp.elements[1].position = p1, p2
    r.color_ramp.elements[0].color = (*c1, 1)
    r.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _bump(nt, bsdf, fac, strength):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    nt.links.new(fac, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def _multiply(nt, a, b):
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = 'RGBA'
    mx.blend_type = 'MULTIPLY'
    mx.inputs[0].default_value = 1.0
    nt.links.new(a, mx.inputs[6])
    nt.links.new(b, mx.inputs[7])
    return mx.outputs[2]


def mat_wall(tint=(0.62, 0.58, 0.47)):
    m, nt, b = _mat("wall")
    v = _coords(nt)
    stains = _ramp_mix(nt, _noise(nt, v, 1.3, 8, 0.7), [t * 0.62 for t in tint], tint, 0.35, 0.62)
    grime = _ramp_mix(nt, _noise(nt, v, 9.0, 10, 0.75), (0.8, 0.78, 0.72), (1, 1, 1), 0.3, 0.6)
    # darker toward the floor (scuffs, mop splash)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(v, sep.inputs[0])
    low = _ramp_mix(nt, sep.outputs["Z"], (0.55, 0.52, 0.47), (1, 1, 1), 0.0, 0.35)
    nt.links.new(_multiply(nt, _multiply(nt, stains, grime), low), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.75
    _bump(nt, b, _noise(nt, v, 180, 4, 0.5), 0.08)
    return m


def mat_carpet():
    m, nt, b = _mat("carpet")
    v = _coords(nt)
    wear = _ramp_mix(nt, _noise(nt, v, 0.9, 6, 0.6), (0.06, 0.065, 0.075), (0.13, 0.14, 0.16), 0.3, 0.7)
    fleck = _ramp_mix(nt, _noise(nt, v, 260, 2, 0.5), (0.7, 0.7, 0.7), (1.1, 1.1, 1.1), 0.3, 0.7)
    nt.links.new(_multiply(nt, wear, fleck), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    _bump(nt, b, _noise(nt, v, 400, 2, 0.5), 0.35)
    return m


def mat_ceiling():
    m, nt, b = _mat("ceiling")
    v = _coords(nt)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 1.2
    br.inputs["Row Height"].default_value = 0.6
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Color1"].default_value = (0.62, 0.61, 0.56, 1)
    br.inputs["Color2"].default_value = (0.55, 0.54, 0.49, 1)
    br.inputs["Mortar"].default_value = (0.25, 0.25, 0.24, 1)
    nt.links.new(v, br.inputs["Vector"])
    water = _ramp_mix(nt, _noise(nt, v, 2.2, 8, 0.7), (0.62, 0.52, 0.36), (1, 1, 1), 0.62, 0.68)
    nt.links.new(_multiply(nt, br.outputs["Color"], water), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    _bump(nt, b, _noise(nt, v, 120, 3, 0.5), 0.15)
    return m


def mat_flat(name, rgb, rough=0.6, metal=0.0):
    m, nt, b = _mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def mat_wood():
    m, nt, b = _mat("wood")
    v = _coords(nt)
    w = nt.nodes.new("ShaderNodeTexWave")
    w.inputs["Scale"].default_value = 9.0
    w.inputs["Distortion"].default_value = 3.0
    w.inputs["Detail"].default_value = 3.0
    w.bands_direction = 'Z'
    nt.links.new(v, w.inputs["Vector"])
    col = _ramp_mix(nt, w.outputs["Fac"], (0.13, 0.075, 0.04), (0.2, 0.12, 0.065), 0.2, 0.8)
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.45
    return m


def mat_emit(name, rgb, strength, diffuse=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    e.inputs["Strength"].default_value = strength
    out = e.outputs[0]
    if diffuse:
        d = nt.nodes.new("ShaderNodeBsdfDiffuse")
        d.inputs["Color"].default_value = (*diffuse, 1)
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(out, add.inputs[0])
        nt.links.new(d.outputs[0], add.inputs[1])
        out = add.outputs[0]
    nt.links.new(out, nt.nodes["Material Output"].inputs[0])
    return m, e


def mat_image(path, strength=1.0):
    """Emissive image (for the CRT screen)."""
    m = bpy.data.materials.new("screen")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Strength"].default_value = strength
    nt.links.new(tex.outputs[0], e.inputs[0])
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
    return m


# ---------------------------------------------------------------- geometry
def box(name, loc, size, m, rot=(0, 0, 0)):
    """Axis-aligned box by centre + full size, scale applied so Object coords are metres."""
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if m:
        o.data.materials.append(m)
    return o


def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    if m:
        o.data.materials.append(m)
    return o


def text(body, loc, rot, size, m, align='CENTER'):
    cu = bpy.data.curves.new("t", 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.extrude = 0.002
    o = bpy.data.objects.new("t", cu)
    o.location = loc
    o.rotation_euler = rot
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    return o


class Mats:
    def __init__(self):
        self.wall = mat_wall()
        self.carpet = mat_carpet()
        self.ceiling = mat_ceiling()
        self.wood = mat_wood()
        self.frame = mat_flat("frame", (0.18, 0.17, 0.15), 0.4, 0.6)
        self.base = mat_flat("baseboard", (0.035, 0.03, 0.028), 0.5)
        self.plaque = mat_flat("plaque", (0.02, 0.02, 0.025), 0.3)
        self.white = mat_flat("lettering", (0.8, 0.8, 0.75), 0.4)
        self.brass = mat_flat("brass", (0.55, 0.42, 0.2), 0.3, 1.0)
        self.red = mat_flat("red", (0.45, 0.02, 0.02), 0.35)
        self.steel = mat_flat("steel", (0.45, 0.45, 0.45), 0.5, 1.0)
        self.cork = mat_flat("cork", (0.35, 0.24, 0.13), 0.9)
        self.paper = mat_flat("paper", (0.75, 0.74, 0.7), 0.8)
        self.black = mat_flat("black", (0.01, 0.01, 0.01), 0.5)
        self.desk = mat_flat("desk", (0.3, 0.28, 0.24), 0.5)
        self.grey = mat_flat("grey", (0.2, 0.2, 0.21), 0.6)


def door(M, x_side, y, label, open_angle=0.0):
    """Office door on the wall at x_side (-1 or +1), centred at y."""
    wx = x_side * HALL_W / 2
    inward = -x_side  # direction into the corridor
    # frame
    for dy in (-0.5, 0.5):
        box("jamb", (wx + inward * 0.02, y + dy, 1.07), (0.08, 0.07, 2.14), M.frame)
    box("head", (wx + inward * 0.02, y, 2.17), (0.08, 1.07, 0.07), M.frame)
    # dark opening behind the door (so an open door shows a void)
    box("void", (wx - inward * 0.3, y, 1.07), (0.5, 0.94, 2.1), M.black)
    # leaf, hinged at y-0.47
    bpy.ops.object.empty_add(location=(wx + inward * 0.005, y - 0.465, 0))
    hinge = bpy.context.object
    leaf = box("door", (wx + inward * 0.005, y, 1.06), (0.045, 0.92, 2.1), M.wood)
    knob = cyl("knob", (wx + inward * 0.04, y + 0.36, 1.0), 0.03, 0.06, M.brass, rot=(0, math.pi / 2, 0))
    for o in (leaf, knob):
        o.parent = hinge
        o.matrix_parent_inverse = hinge.matrix_world.inverted()
    hinge.rotation_euler[2] = -inward * open_angle
    # number plaque beside the door
    if label:
        py = y + 0.72
        box("plaque", (wx + inward * 0.012, py, 1.55), (0.012, 0.2, 0.09), M.plaque)
        text(label, (wx + inward * 0.02, py, 1.55), (math.pi / 2, 0, inward * math.pi / 2), 0.07, M.white)
    return hinge


class Fixture:
    """Recessed 2x4 fluorescent troffer: emissive diffuser + area light, animatable."""
    def __init__(self, y, x=0.0, z=HALL_H, power=90.0, mode="ok"):
        self.mat, self.emit = mat_emit("tube", (0.92, 1.0, 0.9), 6.0, diffuse=(0.55, 0.56, 0.52))
        self.panel = box("troffer", (x, y, z - 0.005), (0.6, 1.2, 0.01), self.mat)
        box("trim", (x, y, z - 0.002), (0.66, 1.26, 0.006), mat_flat("trim", (0.5, 0.5, 0.48), 0.4))
        d = bpy.data.lights.new("fl", 'AREA')
        d.shape = 'RECTANGLE'
        d.size, d.size_y = 0.55, 1.15
        d.color = (0.9, 1.0, 0.88)
        d.energy = power
        self.light = d
        o = bpy.data.objects.new("fl", d)
        o.location = (x, y, z - 0.02)
        bpy.context.scene.collection.objects.link(o)
        self.power, self.mode = power, mode

    def level_at(self, f):
        m = self.mode
        if m == "dead":
            return 0.0
        if m == "ok":
            return 0.08 if random.random() < 0.015 else 1.0
        if m == "bad":
            return random.choice([0.0, 0.05, 0.6, 1.0]) if random.random() < 0.35 else 1.0
        if m == "dying":
            return 0.0 if random.random() < 0.6 else random.uniform(0.1, 0.5)
        return 1.0

    def animate(self, f0, f1, override=None):
        for f in range(f0, f1 + 1):
            lv = override(f) if override and override(f) is not None else self.level_at(f)
            self.set(lv, f)

    def set(self, lv, frame=None):
        self.light.energy = self.power * lv
        self.emit.inputs["Strength"].default_value = 6.0 * lv
        if frame is not None:
            self.light.keyframe_insert("energy", frame=frame)
            self.emit.inputs["Strength"].keyframe_insert("default_value", frame=frame)


def hallway(M, n_doors=9, end_label=None, end_open=0.0, modes=None, start_number=301, seed=3, tail=2.5, void=True, power=75.0):
    """Corridor running +y from the elevator lobby (y=0). Returns (length, fixtures, end_door)."""
    random.seed(seed)
    L = 2.5 + n_doors * DOOR_SPACING / 2 + tail
    W, H = HALL_W, HALL_H
    box("floor", (0, L / 2 - 2, -0.05), (W + 0.4, L + 4, 0.1), M.carpet)
    box("ceiling", (0, L / 2 - 2, H + 0.05), (W + 0.4, L + 4, 0.1), M.ceiling)
    box("wallL", (-W / 2 - 0.05, L / 2, H / 2), (0.1, L, H), M.wall)
    box("wallR", (W / 2 + 0.05, L / 2, H / 2), (0.1, L, H), M.wall)
    for s_ in (-1, 1):  # end wall with a doorway
        box("endwall", (s_ * (W / 4 + 0.27), L + 0.05, H / 2), (W / 2 - 0.54, 0.1, H), M.wall)
    box("endwall_top", (0, L + 0.05, 2.2 + (H - 2.2) / 2), (1.08, 0.1, H - 2.2), M.wall)
    for s in (-1, 1):
        box("base", (s * (W / 2 - 0.005), L / 2, 0.05), (0.012, L, 0.1), M.base)
    # doors alternate sides, odd numbers left
    for i in range(n_doors):
        side = -1 if i % 2 == 0 else 1
        y = 2.5 + (i // 2) * DOOR_SPACING + (DOOR_SPACING / 2 if side == 1 else 0) + 0.8
        door(M, side, y, str(start_number + i))
    end = door_end(M, L, end_label, end_open, void)
    # dressing: extinguisher cabinet, bulletin board, exit sign, water fountain
    box("ext_cab", (-W / 2 + 0.02, 1.7, 1.2), (0.04, 0.35, 0.7), M.red)
    cyl("ext", (-W / 2 + 0.12, 1.7, 1.05), 0.07, 0.45, M.red)
    box("board", (W / 2 - 0.01, 6.5, 1.45), (0.02, 1.2, 0.8), M.cork)
    for k in range(5):
        box("note", (W / 2 - 0.025, 6.15 + k * 0.17 + random.uniform(-0.03, 0.03), 1.45 + random.uniform(-0.25, 0.25)),
            (0.004, 0.15, 0.2), M.paper, rot=(random.uniform(-0.1, 0.1), 0, 0))
    em, _ = mat_emit("exit", (1, 0.05, 0.03), 5)
    box("exit", (0, L - 0.08, H - 0.2), (0.4, 0.06, 0.16), M.frame)
    text("EXIT", (0, L - 0.12, H - 0.2), (math.pi / 2, 0, 0), 0.1, em)
    box("fountain", (W / 2 - 0.2, L - 3.5, 0.85), (0.35, 0.45, 0.25), M.steel)
    # lights every 3.2m
    fixtures = []
    ys = [1.0 + k * 3.2 for k in range(int((L - 1.0) / 3.2) + 1)]
    for k, y in enumerate(ys):
        mode = (modes[k] if modes and k < len(modes) else "ok")
        fixtures.append(Fixture(y, mode=mode, power=power))
    return L, fixtures, end


def door_end(M, L, label, open_angle, void=True):
    """The unnumbered door at the end of the hall (faces -y)."""
    y = L - 0.02
    for dx in (-0.5, 0.5):
        box("jamb", (dx, y, 1.07), (0.07, 0.08, 2.14), M.frame)
    box("head", (0, y, 2.17), (1.07, 0.08, 0.07), M.frame)
    if void:
        box("void", (0, y + 0.4, 1.07), (1.0, 0.5, 2.2), M.black)
    bpy.ops.object.empty_add(location=(-0.465, y - 0.005, 0))
    hinge = bpy.context.object
    leaf = box("door", (0, y - 0.005, 1.06), (0.92, 0.045, 2.1), M.wood)
    knob = cyl("knob", (0.36, y - 0.04, 1.0), 0.03, 0.06, M.brass, rot=(math.pi / 2, 0, 0))
    for o in (leaf, knob):
        o.parent = hinge
        o.matrix_parent_inverse = hinge.matrix_world.inverted()
    hinge.rotation_euler[2] = open_angle
    if label:
        box("plaque", (0.72, y - 0.012, 1.55), (0.2, 0.012, 0.09), M.plaque)
        text(label, (0.72, y - 0.02, 1.55), (math.pi / 2, 0, 0), 0.07, M.white)
    return hinge


def elevator(M):
    """Elevator car behind y=0 with two sliding doors. Returns (left door, right door)."""
    s = M.steel
    box("car_floor", (0, -1.0, -0.04), (1.6, 1.8, 0.08), mat_flat("elev_floor", (0.1, 0.09, 0.08), 0.7))
    box("car_ceiling", (0, -1.0, 2.35), (1.6, 1.8, 0.1), s)
    box("car_back", (0, -1.95, 1.2), (1.6, 0.1, 2.5), s)
    box("car_l", (-0.85, -1.0, 1.2), (0.1, 1.8, 2.5), s)
    box("car_r", (0.85, -1.0, 1.2), (0.1, 1.8, 2.5), s)
    box("lobby_wall_l", (-0.95, 0.0, 1.3), (0.9, 0.12, 2.6), M.wall)
    box("lobby_wall_r", (0.95, 0.0, 1.3), (0.9, 0.12, 2.6), M.wall)
    box("lobby_head", (0, 0.0, 2.45), (1.0, 0.12, 0.3), M.wall)
    em, _ = mat_emit("car_light", (1, 0.95, 0.85), 3)
    box("car_panel", (0, -1.0, 2.29), (1.0, 1.0, 0.02), em)
    d = bpy.data.lights.new("carl", 'AREA')
    d.size = 1.0
    d.energy = 25
    o = bpy.data.objects.new("carl", d)
    o.location = (0, -1.0, 2.25)
    bpy.context.scene.collection.objects.link(o)
    dl = box("edoor_l", (-0.25, -0.08, 1.05), (0.5, 0.04, 2.1), s)
    dr = box("edoor_r", (0.25, -0.08, 1.05), (0.5, 0.04, 2.1), s)
    return dl, dr


def figure(loc, height=2.25, facing=math.pi, reach=0.0, head_tilt=0.0, toward=None):
    """Tall, thin humanoid: skin-modifier skeleton for the body, pale featureless head.
    facing = z-rotation (pi faces -y, toward the elevator). reach 0..1 lifts the arms forward."""
    k = height / 2.25
    r = reach
    J = [  # (x, y, z, rx, ry)
        (0, 0, 1.05, 0.17, 0.12), (0, 0, 1.28, 0.14, 0.1), (0, 0, 1.56, 0.19, 0.12),
        (0, 0, 1.84, 0.055, 0.055), (0, -0.01, 1.93, 0.06, 0.06),
        (-0.22, 0, 1.74, 0.07, 0.07), (0.22, 0, 1.74, 0.07, 0.07),
        (-0.3, 0.02 - 0.35 * r, 1.3 + 0.25 * r, 0.05, 0.05), (0.3, 0.02 - 0.35 * r, 1.3 + 0.25 * r, 0.05, 0.05),
        (-0.33, -0.02 - 0.75 * r, 0.85 + 0.6 * r, 0.038, 0.038), (0.33, -0.02 - 0.75 * r, 0.85 + 0.6 * r, 0.038, 0.038),
        (-0.34, -0.04 - 0.98 * r, 0.6 + 0.8 * r, 0.025, 0.03), (0.34, -0.04 - 0.98 * r, 0.6 + 0.8 * r, 0.025, 0.03),
        (-0.11, 0, 1.0, 0.09, 0.09), (0.11, 0, 1.0, 0.09, 0.09),
        (-0.12, 0, 0.55, 0.065, 0.065), (0.12, 0, 0.55, 0.065, 0.065),
        (-0.12, 0.02, 0.08, 0.045, 0.045), (0.12, 0.02, 0.08, 0.045, 0.045),
        (-0.12, -0.15, 0.03, 0.04, 0.03), (0.12, -0.15, 0.03, 0.04, 0.03),
    ]
    E = [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5), (2, 6), (5, 7), (6, 8), (7, 9), (8, 10), (9, 11), (10, 12),
         (0, 13), (0, 14), (13, 15), (14, 16), (15, 17), (16, 18), (17, 19), (18, 20)]
    me = bpy.data.meshes.new("fig")
    me.from_pydata([(x * k, y * k, z * k) for x, y, z, _, _ in J], E, [])
    body = bpy.data.objects.new("fig", me)
    bpy.context.scene.collection.objects.link(body)
    sk = body.modifiers.new("skin", 'SKIN')
    body.modifiers.new("sub", 'SUBSURF').levels = 2
    body.modifiers["sub"].render_levels = 2
    for i, (_, _, _, rx, ry) in enumerate(J):
        sv = me.skin_vertices[0].data[i]
        sv.radius = (rx * k, ry * k)
        sv.use_root = (i == 0)
    body.data.materials.append(mat_flat("skin_dark", (0.014, 0.013, 0.013), 0.5))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, -0.015 * k, 2.05 * k), segments=32, ring_count=16)
    head = bpy.context.object
    head.scale = (0.105 * k, 0.12 * k, 0.155 * k)
    head.data.materials.append(mat_flat("skin_pale", (0.3, 0.285, 0.26), 0.45))
    bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update()
    for s in (-1, 1):  # sunken black eyes, parented to the head so they follow its tilt
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(s * 0.04 * k, -0.125 * k, 2.08 * k), segments=16, ring_count=8)
        eye = bpy.context.object
        eye.scale = (0.026 * k, 0.012 * k, 0.017 * k)
        eye.data.materials.append(mat_flat("socket", (0.0, 0.0, 0.0), 0.9))
        eye.parent = head
        eye.matrix_parent_inverse = head.matrix_world.inverted()
    head.rotation_euler[0] = head_tilt
    parts = [body, head]
    bpy.ops.object.empty_add(location=loc)
    root = bpy.context.object
    for o in parts:
        o.parent = root
    if toward is not None:
        root.rotation_euler[2] = math.atan2(toward[0] - loc[0], -(toward[1] - loc[1]))
    else:
        root.rotation_euler[2] = facing - math.pi
    return root


def office(M, origin=(0, 0, 0)):
    """Dark open-plan office behind the end door. origin = doorway centre; room extends +y."""
    ox, oy, oz = origin
    W, D, H = 8.0, 9.0, HALL_H
    box("o_floor", (ox, oy + D / 2, -0.05), (W, D, 0.1), M.carpet)
    box("o_ceiling", (ox, oy + D / 2, H + 0.05), (W, D, 0.1), M.ceiling)
    box("o_back", (ox, oy + D + 0.05, H / 2), (W, 0.1, H), M.wall)
    box("o_l", (ox - W / 2, oy + D / 2, H / 2), (0.1, D, H), M.wall)
    box("o_r", (ox + W / 2, oy + D / 2, H / 2), (0.1, D, H), M.wall)
    for s in (-1, 1):
        box("o_front", (ox + s * (W / 4 + 0.25), oy, H / 2), (W / 2 - 0.5, 0.1, H), M.wall)
    for row in range(3):
        for col in (-1, 1):
            x, y = ox + col * 2.0, oy + 2.2 + row * 2.4
            box("desk", (x, y, 0.74), (1.5, 0.75, 0.04), M.desk)
            for dx in (-0.7, 0.7):
                box("leg", (x + dx, y, 0.37), (0.04, 0.7, 0.74), M.grey)
            box("partition", (x, y + 0.45, 0.6), (1.6, 0.05, 1.2), mat_flat("fabric", (0.2, 0.22, 0.24), 0.95))
            box("chair_seat", (x + 0.2, y - 0.6, 0.48), (0.45, 0.45, 0.07), M.grey)
            box("chair_back", (x + 0.2, y - 0.82, 0.8), (0.42, 0.05, 0.5), M.grey)
            cyl("chair_post", (x + 0.2, y - 0.6, 0.24), 0.025, 0.48, M.steel)
            for _ in range(random.randint(1, 4)):
                box("paper", (x + random.uniform(-0.6, 0.6), y + random.uniform(-0.25, 0.2), 0.765),
                    (0.21, 0.29, 0.003), M.paper, rot=(0, 0, random.uniform(-0.5, 0.5)))
    box("cabinet", (ox + W / 2 - 0.35, oy + D - 1.5, 0.7), (0.6, 0.5, 1.4), M.grey)
    box("cabinet", (ox + W / 2 - 0.35, oy + D - 2.2, 0.7), (0.6, 0.5, 1.4), M.grey)
    return (ox, oy, D)


def crt(M, loc, rot_z, screen_img=None, strength=1.6):
    """Wood-grain CRT television; screen shows screen_img (or static-grey)."""
    x, y, z = loc
    grp = []
    grp.append(box("crt_body", (0, 0, 0.22), (0.62, 0.5, 0.46), M.wood))
    grp.append(box("crt_bezel", (0, -0.252, 0.24), (0.52, 0.01, 0.4), M.black))
    if screen_img:
        sm = mat_image(screen_img, strength)
    else:
        sm, _ = mat_emit("static", (0.6, 0.6, 0.65), strength)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.26, 0.25), rotation=(math.pi / 2, 0, 0))
    scr = bpy.context.object
    scr.scale = (0.44, 0.33, 1)
    scr.data.materials.append(sm)
    grp.append(scr)
    bpy.ops.object.empty_add(location=loc)
    root = bpy.context.object
    for o in grp:
        o.parent = root
    root.rotation_euler[2] = rot_z
    glow = bpy.data.lights.new("crt_glow", 'AREA')
    glow.size = 0.45
    glow.energy = 6 * strength
    glow.color = (0.7, 0.75, 0.9)
    go = bpy.data.objects.new("crt_glow", glow)
    go.parent = root
    go.location = (0, -0.35, 0.25)
    go.rotation_euler = (-math.pi / 2, 0, 0)
    bpy.context.scene.collection.objects.link(go)
    return root


# ---------------------------------------------------------------- camera
def camera(lens=22):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    bpy.context.scene.camera = cam
    cam.rotation_mode = 'XYZ'
    return cam


def look(cam, pos, target, roll=0.0):
    cam.location = pos
    d = Vector(target) - Vector(pos)
    q = d.to_track_quat('-Z', 'Y')
    e = q.to_euler()
    e.rotate_axis('Z', roll)
    cam.rotation_euler = e


def key_cam(cam, f, pos, target, roll=0.0):
    prev = cam.rotation_euler.copy() if cam.animation_data else None
    look(cam, pos, target, roll)
    if prev is not None:
        for i in range(3):
            while cam.rotation_euler[i] - prev[i] > math.pi:
                cam.rotation_euler[i] -= 2 * math.pi
            while cam.rotation_euler[i] - prev[i] < -math.pi:
                cam.rotation_euler[i] += 2 * math.pi
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)


def handheld(cam, strength=1.0, walking=False):
    """Layer procedural shake on the camera's keyed motion."""
    ad = cam.animation_data
    for fc in ad.action.fcurves:
        if fc.data_path == "rotation_euler":
            m = fc.modifiers.new('NOISE')
            m.scale, m.strength, m.phase = 22, 0.035 * strength, random.uniform(0, 100)
            m2 = fc.modifiers.new('NOISE')
            m2.scale, m2.strength, m2.phase = 4, 0.006 * strength, random.uniform(0, 100)
        if fc.data_path == "location" and fc.array_index == 2 and walking:
            m = fc.modifiers.new('NOISE')
            m.scale, m.strength, m.phase = 7, 0.05 * strength, random.uniform(0, 100)
        if fc.data_path == "location" and fc.array_index == 0:
            m = fc.modifiers.new('NOISE')
            m.scale, m.strength, m.phase = 30, 0.03 * strength, random.uniform(0, 100)


def linear_keys(obj):
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
