# Safar Pahad Parivar - import the whole SFX library into an 'SPP SFX' bin (one sub-bin per category).
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

cat = S.catalog()
if cat is not None:
    n = S.Pool(proj).import_all(cat)
    print("Imported %d new sounds into the 'SPP SFX' bin (%d in the library)." % (n, len(cat)))
    print("Loops are named *_LOOP_*: use 'SFX - Loop Fill (In to Out)' to repeat one for any length.")
