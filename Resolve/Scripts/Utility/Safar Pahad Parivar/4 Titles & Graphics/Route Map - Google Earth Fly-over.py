# Safar Pahad Parivar - make Google Earth Studio fly-overs of this timeline's route (3D satellite view, camera follows
# the road from behind and above, clearing the ridges).
# Run 'Route Map - Build from Timeline' first. One fly-over for the whole trip, plus one per chapter for every
# SPP Route Map title that has 'from stop' / 'to stop' set.
# Output: <trip>\Route Maps\<timeline>\Google Earth\  (.esp = Earth Studio project, .kml = route line + stop pins)
# Then in Chrome: earth.google.com/studio -> New Project -> Import (.esp) -> Add > KML (the .kml) -> Render.
import os, re, sys
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
import subprocess
TOOL = os.path.join(_k, "Tools", "spp_earth_studio.py")


def make(rj, out, frm, to, seconds, fps, size, name=None):
    args = [C.PY, TOOL, rj, out, "--seconds", str(seconds), "--fps", str(fps), "--size", size]
    if frm: args += ["--from", frm]
    if to: args += ["--to", to]
    if name: args += ["--name", name]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=0x08000000,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print("  " + (r.stdout.strip() or r.stderr.strip()[-400:]))

proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None


def main():
    if not tl:
        print("Open a timeline first."); return
    trips = [t for t in (C.trip_of(p) for p in C.footage_on(tl)) if t]
    if not trips:
        print("None of the footage is inside a trip folder."); return
    trip = max(set(trips), key=trips.count)
    folder = os.path.join(trip, "Route Maps", re.sub(r'[<>:"/\\|?*]', "_", tl.GetName()))
    rj = os.path.join(folder, "route.json")
    if not os.path.exists(rj):
        print("No route yet - run 'Route Map - Build from Timeline' first."); return
    out = os.path.join(folder, "Google Earth")
    portrait = int(tl.GetSetting("timelineResolutionHeight")) > int(tl.GetSetting("timelineResolutionWidth"))
    size = "2160x3840" if portrait else "3840x2160"
    fps = int(round(float(tl.GetSetting("timelineFrameRate") or 30)))
    print("Making Google Earth Studio fly-overs (a minute or two the first time - terrain heights are downloaded)...")
    if not C.engine_ok():
        return
    make(rj, out, None, None, 60, fps, size, "SPP Flyover - whole trip")
    seen = set()
    for it, tool, track in C.templates_on(tl, "SPP-Route-Map"):
        a, b = (tool.GetInput("DynParamText15") or "").strip(), (tool.GetInput("DynParamText16") or "").strip()
        if (a or b) and (a, b) not in seen:
            seen.add((a, b))
            make(rj, out, a, b, 40, fps, size)
    print("\nNext, in Chrome (Google account needed):")
    print("  1. Open Google Earth Studio, choose 'Import' and pick an .esp from:\n     " + out)
    print("  2. Add > KML > the .kml with the same name (gold road line + stop pins).")
    print("  3. Play it, adjust keyframes if you like, then Render (image sequence, %s, %d fps)." % (size.replace("x", " x "), fps))
    print("  4. Import the image sequence into Resolve. Keep the 'Google Earth' credit on screen (Google's rule).")
    try:
        os.startfile(out)
    except Exception:
        pass


main()
