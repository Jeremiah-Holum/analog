# Dark hallway, flickering bulb, slow push-in; a figure appears at the far end.
import bpy, math, random, os
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
OUT = os.environ.get("OUT", "/tmp/frames")
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = 320, 240
sc.frame_start, sc.frame_end = 1, 120
sc.render.fps = 24
sc.render.filepath = OUT + "/f_"
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0, 0, 0)

def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m

def box(loc, scale, m):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object
    o.scale = scale; o.data.materials.append(m); return o

wall = mat("wall", (0.35, 0.33, 0.25)); floor = mat("floor", (0.12, 0.1, 0.08))
dark = mat("dark", (0.02, 0.02, 0.02)); door = mat("door", (0.2, 0.12, 0.07))
L = 20
box((0, L/2, -0.05), (1.2, L/2, 0.05), floor)
box((0, L/2, 2.6), (1.2, L/2, 0.05), wall)
box((-1.25, L/2, 1.3), (0.05, L/2, 1.35), wall)
box((1.25, L/2, 1.3), (0.05, L/2, 1.35), wall)
box((0, L + 0.05, 1.3), (1.2, 0.05, 1.35), wall)
box((0, L, 1.0), (0.45, 0.08, 1.0), door)
for y in range(3, L, 4):  # side doorframes
    box((-1.2, y, 1.0), (0.06, 0.45, 1.0), door)

# the figure: hidden until frame 70
bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.6, location=(0.3, L - 2.5, 0.8))
body = bpy.context.object; body.data.materials.append(dark)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(0.3, L - 2.5, 1.75))
head = bpy.context.object; head.data.materials.append(dark)
for o in (body, head):
    for f, hide in ((1, True), (69, True), (70, False)):
        o.hide_render = hide; o.keyframe_insert("hide_render", frame=f)

# flickering bulbs
lights = []
for y in (4, 10, 19):
    d = bpy.data.lights.new("bulb", 'POINT'); d.color = (1, 0.85, 0.6); d.shadow_soft_size = 0.1
    o = bpy.data.objects.new("bulb", d); o.location = (0, y, 2.45); sc.collection.objects.link(o)
    lights.append(d)
for f in range(1, 121):
    for i, d in enumerate(lights):
        base = 400 if i < 2 else 300
        d.energy = base * (0.05 if random.random() < 0.12 else random.uniform(0.8, 1.0))
        if i == 2 and 66 <= f <= 72: d.energy = 0  # blackout at the far end as the figure appears
        d.keyframe_insert("energy", frame=f)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.lens = 24; sc.camera = cam
for f, y in ((1, 0.5), (120, 5.5)):
    cam.location = (0.15, y, 1.55); cam.rotation_euler = (math.radians(88), 0, 0)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
# handheld wobble
for f in range(1, 121, 6):
    cam.rotation_euler = (math.radians(88 + random.uniform(-0.8, 0.8)), math.radians(random.uniform(-0.6, 0.6)),
                          math.radians(random.uniform(-0.8, 0.8)))
    cam.keyframe_insert("rotation_euler", frame=f)
bpy.ops.render.render(animation=True)
