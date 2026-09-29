# Safar Pahad Parivar - make SPP titles behave like Resolve's own titles when you change their length:
# the entrance keeps its timing at the start, the exit always finishes on the last frame, the hold in between
# stretches or shrinks.  Run it once after adding titles - from then on it's automatic (Ctrl+D, dragging the end...).
# (Fill from GPS, Chapters and Auto Sound for Titles do this too.)  Titles can be shortened, not made longer than
# their default length.
import os, sys
try:
    resolve
except NameError:
    try:
        resolve = app.GetResolve()
    except Exception:
        resolve = bmd.scriptapp("Resolve")
_h = os.path.join(os.environ["APPDATA"], r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")
_k = open(os.path.join(_h, "kit_path.txt"), encoding="utf-8-sig").read().strip()
sys.path.insert(0, os.path.join(_k, "Tools"))
import spp_resolve_common as C

proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
if not tl:
    print("Open a timeline first.")
else:
    C.follow_clip(tl)
