# Safar Pahad Parivar - find the clips of this trip that have windshield / window reflections.
# First run: scans every video of the trip in a background window (a few minutes; later runs only do new clips).
# Run again when it's done: media pool clips get a colour - ORANGE = strong reflection, YELLOW = some -
# and a picture of the worst ones opens.  Full list: <trip>\_spp_clean\reflection_report.csv
import json, os, subprocess, sys
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
import spp_reflection_resolve as R

proj = resolve.GetProjectManager().GetCurrentProject()
trip = M.trip_from_project(proj) if proj else None
VID = (".mp4", ".mov")
if not trip:
    print("Couldn't find the trip folder - import some of the trip's footage into this project first.")
elif C.engine_ok():
    d = os.path.join(trip, "_spp_clean")
    cache_p = os.path.join(d, "scan.json")
    cache = json.load(open(cache_p, encoding="utf-8")) if os.path.exists(cache_p) else {}
    vids = [os.path.join(p, f) for p, _, fs in os.walk(os.path.join(trip, "Footage")) for f in fs if f.lower().endswith(VID)]
    missing = [v for v in vids if v not in cache]
    running = os.path.exists(os.path.join(d, "scan_running.txt"))
    if missing and not running:
        os.makedirs(d, exist_ok=True)
        bat = os.path.join(d, "scan.bat")
        with open(bat, "w", encoding="utf-8") as fh:
            fh.write('@echo off\nchcp 65001 >nul\nset PYTHONIOENCODING=utf-8\ntitle SPP Reflection scan\necho running> "%s"\n'
                     '"%s" "%s" scan "%s"\ndel "%s"\necho.\necho Done - run Reflection - Scan Trip in Resolve again. You can close this window.\npause >nul\n'
                     % (os.path.join(d, "scan_running.txt"), C.PY, R.ENGINE, trip, os.path.join(d, "scan_running.txt")))
        subprocess.Popen('start "SPP Reflection scan" cmd /c "%s"' % bat, shell=True)
        print("Scanning %d clip(s) of %s in the background window 'SPP Reflection scan'." % (len(missing), os.path.basename(trip)))
        print("Run this script again when it says Done.")
    elif missing:
        print("The scan is still running (%d of %d clips done) - run again when its window says Done." % (len(vids) - len(missing), len(vids)))
    if cache:
        idx = M.pool_index(proj.GetMediaPool())
        strong = some = 0
        for path, v in cache.items():
            s = v.get("score", 0)
            it = idx.get(os.path.normcase(path))
            if not it:
                continue
            if s >= 4:
                it.SetClipColor("Orange"); strong += 1
            elif s >= 1.5:
                it.SetClipColor("Yellow"); some += 1
        top = sorted(((v.get("score", 0), k) for k, v in cache.items()), reverse=True)[:12]
        print("Media pool: %d clip(s) ORANGE (strong reflection), %d YELLOW (some)." % (strong, some))
        print("Worst ones:")
        for s, k in top:
            if s >= 1.5:
                print("  %5.1f  %s" % (s, os.path.basename(k)))
        sheet = os.path.join(d, "reflection_sheet.jpg")
        if os.path.exists(sheet) and not missing:
            os.startfile(sheet)
        print("Clean them: put them on the timeline, select, run 'Reflection - Clean Selected Clips'.")
