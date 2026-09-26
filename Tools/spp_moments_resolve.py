"""Shared helpers for the 'Moments - ...' Resolve menu scripts (runs inside Resolve's Python)."""
import json, os, subprocess
import spp_resolve_common as C

COLORS = {"laugh": "Yellow", "kids": "Pink", "shout": "Red", "cheer": "Fuchsia", "sing": "Purple", "word": "Green", "talk": "Blue"}
TAG = "spp_moment"


def all_clips(folder, out=None):
    out = [] if out is None else out
    out += folder.GetClipList() or []
    for f in folder.GetSubFolderList() or []:
        all_clips(f, out)
    return out


def pool_index(mp):
    return {os.path.normcase(c.GetClipProperty("File Path") or ""): c for c in all_clips(mp.GetRootFolder())
            if c.GetClipProperty("File Path")}


def trip_from_project(proj):
    """The trip folder of the footage used in this project (timeline first, then the media pool)."""
    tl = proj.GetCurrentTimeline()
    paths = []
    if tl:
        for tr in range(1, tl.GetTrackCount("video") + 1):
            for it in tl.GetItemListInTrack("video", tr) or []:
                m = it.GetMediaPoolItem()
                if m:
                    paths.append(m.GetClipProperty("File Path") or "")
    paths += list(pool_index(proj.GetMediaPool()).keys())
    for p in paths:
        t = C.trip_of(p) if p else None
        if t:
            return t
    return None


def load(trip):
    p = os.path.join(trip, "_spp_moments", "moments.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def ensure_items(mp, files):
    """Media pool items for these files (imports the missing ones into 'SPP Moments Footage')."""
    idx = pool_index(mp)
    miss = [f for f in files if os.path.normcase(f) not in idx and os.path.exists(f)]
    if miss:
        root = mp.GetRootFolder()
        b = next((f for f in root.GetSubFolderList() if f.GetName() == "SPP Moments Footage"), None) or mp.AddSubFolder(root, "SPP Moments Footage")
        prev = mp.GetCurrentFolder()
        mp.SetCurrentFolder(b)
        mp.ImportMedia(miss)
        mp.SetCurrentFolder(prev)
        idx = pool_index(mp)
    return idx


def fps_of(item, default=30.0):
    try:
        return float(item.GetClipProperty("FPS") or default)
    except Exception:
        return default


def build_timeline(proj, name, spans, handle=0.5):
    """New timeline with the given [(file, a, b, label, note, kind)] spans, in order, each with a marker."""
    mp = proj.GetMediaPool()
    idx = ensure_items(mp, sorted({s[0] for s in spans}))
    tl = mp.CreateEmptyTimeline(name)
    if not tl:
        print("Could not create timeline", name); return None
    proj.SetCurrentTimeline(tl)
    tfps = float(tl.GetSetting("timelineFrameRate"))
    pos = 0
    n = 0
    for f, a, b, label, note, kind in spans:
        it = idx.get(os.path.normcase(f))
        if not it:
            continue
        fps = fps_of(it)
        s, e = max(0, int((a - handle) * fps)), int((b + handle) * fps)
        res = mp.AppendToTimeline([{"mediaPoolItem": it, "startFrame": s, "endFrame": e}]) or []
        if res:
            tl.AddMarker(pos, COLORS.get(kind, "Blue"), label[:60], (note or "")[:500], 1, TAG)
            pos += int(round((e - s) / fps * tfps))
            n += 1
    print("Timeline '%s': %d clips" % (name, n))
    return tl


def run_analysis(trip):
    """Start the analysis in the background (it can take a while) and return the log path."""
    logp = os.path.join(trip, "_spp_moments", "analyse_log.txt")
    os.makedirs(os.path.dirname(logp), exist_ok=True)
    bat = os.path.join(trip, "_spp_moments", "analyse.bat")
    with open(bat, "w", encoding="utf-8") as fh:
        fh.write('@echo off\nchcp 65001 >nul\nset PYTHONIOENCODING=utf-8\n"%s" "%s" "%s" > "%s" 2>&1\n' % (
            C.PY, os.path.join(C.KIT, "Tools", "spp_moments.py"), trip, logp))
    subprocess.Popen('start "SPP Moments" /min cmd /c "%s"' % bat, shell=True)
    return logp
