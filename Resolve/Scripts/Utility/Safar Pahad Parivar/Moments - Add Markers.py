# Safar Pahad Parivar - put a coloured marker on every found moment, on the source clips in the Media Pool
# (they show in the source viewer and on the clips in any timeline).  Colours: Yellow laughter, Pink kids talking,
# Red shout/excitement, Fuchsia cheering, Purple singing, Green reaction words.  Re-running replaces the old markers.
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
import spp_moments_resolve as M
proj = resolve.GetProjectManager().GetCurrentProject()
trip = M.trip_from_project(proj) if proj else None

data = M.load(trip) if trip else None
if not data:
    print("No moments yet - run 'Moments - Analyse Trip' first.")
else:
    mp = proj.GetMediaPool()
    idx = M.ensure_items(mp, sorted({m["file"] for m in data["moments"]}))
    for it in idx.values():
        it.DeleteMarkerByCustomData(M.TAG)
    n = 0
    for m in data["moments"]:
        it = idx.get(os.path.normcase(m["file"]))
        if not it:
            continue
        fps = M.fps_of(it)
        name = "%s %.2f" % (m["label"], m["score"])
        note = (m["text"] or "") + ("  [%s]" % ", ".join(m["names"]) if m["names"] else "")
        frame, dur = int(m["a"] * fps), max(1, int((m["b"] - m["a"]) * fps))
        while not it.AddMarker(frame, M.COLORS.get(m["kind"], "Blue"), name, note[:500], dur, M.TAG) and frame < dur * 10:
            frame += 1                                   # a marker already sits on that frame
        n += 1
    print("%d moment markers added (open a clip in the source viewer to see them)." % n)
