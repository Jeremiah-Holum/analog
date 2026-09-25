"""Which film the shared engine is working on. FILM=item15 python3 film/build.py -> ITEM 15.
Each film has its own shots/script/edit modules and its own output folder; sound effects are shared."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = os.environ.get("FILM", "film")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

if FILM == "film":
    OUT = os.path.join(ROOT, "out")
    SHOTS, SCRIPT, EDIT, FINAL = "shots", "script", "build", "the_third_floor.mp4"
else:
    OUT = os.path.join(ROOT, "out_" + FILM)
    SHOTS, SCRIPT, EDIT, FINAL = f"{FILM}.shots", f"{FILM}.script", f"{FILM}.edit", f"{FILM}.mp4"
SHARED_SFX = os.path.join(ROOT, "out", "sfx")
