# Safar Pahad Parivar - switch the selected clips between the original and the reflection-cleaned take.
# Nothing selected: switches every cleaned clip on the timeline (a quick before / after of the whole edit).
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
import spp_reflection_resolve as R

proj = resolve.GetProjectManager().GetCurrentProject()
tl = proj.GetCurrentTimeline() if proj else None
if not tl:
    print("Open a timeline first.")
else:
    items = [it for it in (tl.GetSelectedClips() or []) if it.GetTrackTypeAndIndex()[0] == "video"]
    if not items:
        items = [it for t in range(1, tl.GetTrackCount("video") + 1) for it in (tl.GetItemListInTrack("video", t) or [])]
    items = [it for it in items if R.cleaned_take(it)]
    if not items:
        print("No cleaned clips here yet - use 'Reflection - Clean Selected Clips' first.")
    else:
        # all to the same state: if any shows the cleaned take, show originals; otherwise show cleaned
        showing_clean = any(it.GetSelectedTakeIndex() == R.cleaned_take(it) for it in items)
        for it in items:
            it.SelectTakeByIndex(R.original_take(it) if showing_clean else R.cleaned_take(it))
            it.SetClipColor("Orange" if showing_clean else "Teal")
        print("%d clip(s) now show the %s." % (len(items), "ORIGINAL (orange)" if showing_clean else "CLEANED take (teal)"))
