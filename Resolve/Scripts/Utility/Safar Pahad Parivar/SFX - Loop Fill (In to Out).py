# Safar Pahad Parivar - repeat a loop sound for any length.
# 1. Select ONE sound in the media pool (e.g. SPP_Mountain_Wind_LOOP_30s_v01 from the SPP SFX bin).
# 2. Set In and Out on the timeline (I / O keys) where you want it.
# 3. Run this. The loop is laid end-to-end between In and Out on a free "SFX" track (last copy trimmed).
#    The loops are seamless, so the joins are silent. Add a short fade at the ends if you like.
import json, os, sys, zlib
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
import spp_sfx_resolve as S
proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None

def main():
    if not tl:
        print("Open a timeline first."); return
    sel = proj.GetMediaPool().GetSelectedClips() or []
    sel = [m for m in sel if (m.GetClipProperty("Type") or "").lower().startswith("audio") or (m.GetClipProperty("File Path") or "").lower().endswith(".wav")]
    if len(sel) != 1:
        print("Select exactly one sound in the media pool first."); return
    mk = tl.GetMarkInOut() or {}
    io = mk.get("audio") or mk.get("video") or {}
    if "in" not in io or "out" not in io:
        print("Set In and Out on the timeline first (I and O keys)."); return
    fps = float(tl.GetSetting("timelineFrameRate"))
    t0 = tl.GetStartFrame()
    a, b = int(io["in"]), int(io["out"]) + 1
    if not (t0 > 0 and a >= t0):      # marks are relative to the timeline start
        a, b = a + t0, b + t0
    tracks = S.sfx_tracks(tl) or [tl.GetTrackCount("audio")]
    tr = S.free_track(tl, tracks, a, b)
    its = S.loop_fill(proj, tl, sel[0], tr, a, b, fps)
    print("Filled %.1f s with %d copies of %s on %s" % ((b - a) / fps, len(its), sel[0].GetName(), tl.GetTrackName("audio", tr)))


main()
