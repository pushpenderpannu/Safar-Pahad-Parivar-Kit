# Safar Pahad Parivar - listen to every clip of this project's trip and find the family moments
# (laughter, kids shouting / cheering, singing, "wow / papa dekho") + a Hindi transcript of everything said.
# Runs in the background (first time ~20-40 min for a trip; later runs only do new clips).
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

if not trip:
    print("Couldn't find the trip folder - import some of the trip's footage into this project first.")
elif C.engine_ok():
    logp = M.run_analysis(trip)
    print("Analysing the trip in the background:\n  " + trip)
    print("Progress: " + logp)
    print("When it's done: open _spp_moments\\Moments.md, then run 'Moments - Add Markers' / 'Moments - Best Moments Timeline'.")
