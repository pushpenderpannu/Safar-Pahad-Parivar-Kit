# Safar Pahad Parivar - make every SPP title leave with its exit animation, whatever length you gave the clip.
# Resolve doesn't tell a title how long its clip is, so a title trimmed shorter (Ctrl+D, dragging its end) would just
# vanish at the cut. Run this after changing title lengths: each trimmed title's "Animate Out At" is set so the exit
# animation ends on the clip's last frame. Titles back at full length get their default exit again.
# (Fill from GPS, Chapters and Auto Sound for Titles do this too, every time they run.)
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
    C.fit_titles(tl)
