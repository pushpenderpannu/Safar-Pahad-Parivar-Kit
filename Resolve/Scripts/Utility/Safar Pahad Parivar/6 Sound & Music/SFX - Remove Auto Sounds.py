# Safar Pahad Parivar - remove the sounds placed by 'SFX - Auto Sound for Titles' (Lime SPP_ clips).
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

if tl:
    old = []
    for i in range(1, tl.GetTrackCount("audio") + 1):
        old += [it for it in (tl.GetItemListInTrack("audio", i) or [])
                if it.GetClipColor() == S.AUTO_COLOR and (it.GetName() or "").startswith("SPP_")]
    if old:
        tl.DeleteClips(old)
    print("Removed %d auto sound(s)." % len(old))
