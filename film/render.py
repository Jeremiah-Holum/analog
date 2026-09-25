"""Render shots: blender -b -P film/render.py -- <shot> [<shot> ...]
Stills go to out/stills/<name>.png, animations to out/frames/<name>/f_####.png.
Existing output is skipped, so an interrupted run can simply be restarted."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, importlib
import project
shots = importlib.import_module(project.SHOTS)

ROOT = shots.ROOT
names = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for name in names:
    t0 = time.time()
    kind = shots.ALL[name]()
    sc = bpy.context.scene
    if kind[0] == "still":
        out = os.path.join(project.OUT, "stills", name + ".png")
        if os.path.exists(out):
            print(f"[render] skip {name}", flush=True)
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
    elif os.environ.get("PREVIEW"):
        d = os.path.join(project.OUT, "preview", name)
        os.makedirs(d, exist_ok=True)
        sc.render.resolution_percentage = 50
        sc.cycles.samples = 3
        sc.frame_step = 12
        sc.render.filepath = os.path.join(d, "f_")
        bpy.ops.render.render(animation=True)
    else:
        d = os.path.join(project.OUT, "frames", name)
        os.makedirs(d, exist_ok=True)
        sc.render.filepath = os.path.join(d, "f_")
        sc.render.use_overwrite = False
        sc.render.use_placeholder = True
        bpy.ops.render.render(animation=True)
    print(f"[render] done {name} in {time.time() - t0:.0f}s", flush=True)
