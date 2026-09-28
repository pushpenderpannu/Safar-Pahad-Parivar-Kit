"""Shared helpers for the 'Reflection - ...' Resolve menu scripts (runs inside Resolve's Python).

The cleaned copy of a clip goes onto the timeline as a second TAKE of the same timeline clip (Resolve's Take
Selector): same place, same track, same length - titles above it keep working, and the original is always one
click (or 'Reflection - Show Original or Cleaned') away.
"""
import glob, json, os, subprocess, time
import spp_resolve_common as C

ENGINE = os.path.join(C.KIT, "Tools", "spp_reflection.py")
BIN = "SPP Cleaned (reflection)"
STRENGTHS = [("Normal (recommended)", 0.85), ("Gentle", 0.6), ("Strong", 1.0)]


def clean_dir(src):
    trip = C.trip_of(src)
    return os.path.join(trip or os.path.dirname(src), "_spp_clean")


def src_of(item):
    m = item.GetMediaPoolItem() if item else None
    p = m.GetClipProperty("File Path") if m else ""
    return p if p and os.path.exists(p) else ""


def is_cleaned(path):
    return "_spp_clean" in (path or "").replace("/", "\\")


def used_range(item):
    """(first, last) source frame used by this timeline clip."""
    a = int(item.GetSourceStartFrame())
    b = int(item.GetSourceEndFrame())
    if b <= a:                                            # older Resolve: fall back to offsets
        a = int(item.GetLeftOffset() or 0)
        b = a + int(item.GetDuration()) - 1
    return a, b


def find_cleaned(src, a, b, strength=None):
    """An existing cleaned file of this clip that covers frames a..b (at this strength, or any when None)
    -> (path, first frame); the newest one wins."""
    best = (None, None, 0)
    for meta in glob.glob(os.path.join(clean_dir(src), glob.escape(os.path.splitext(os.path.basename(src))[0]) + "__f*.json")):
        try:
            j = json.load(open(meta, encoding="utf-8"))
        except Exception:
            continue
        mp4 = meta[:-5] + ".mp4"
        if (os.path.normcase(j.get("source", "")) == os.path.normcase(os.path.abspath(src)) and os.path.exists(mp4)
                and j["first_frame"] <= a and j["first_frame"] + j.get("frames_written", 0) - 1 >= b
                and (strength is None or abs(j.get("strength", 0.85) - strength) < 0.01)
                and os.path.getmtime(mp4) > best[2]):
            best = (mp4, j["first_frame"], os.path.getmtime(mp4))
    return best[0], best[1]


def cleaned_strength(mp4):
    try:
        return json.load(open(mp4[:-4] + ".json", encoding="utf-8")).get("strength", 0.85)
    except Exception:
        return 0.85


def selected_video_items(tl):
    items = [it for it in (tl.GetSelectedClips() or []) if it.GetTrackTypeAndIndex()[0] == "video"]
    if not items:
        cur = tl.GetCurrentVideoItem()
        items = [cur] if cur else []
    return items


def bin_folder(mp):
    root = mp.GetRootFolder()
    return next((f for f in root.GetSubFolderList() if f.GetName() == BIN), None) or mp.AddSubFolder(root, BIN)


def import_file(mp, path):
    for c in bin_folder(mp).GetClipList() or []:
        if os.path.normcase(c.GetClipProperty("File Path") or "") == os.path.normcase(path):
            return c
    prev = mp.GetCurrentFolder()
    mp.SetCurrentFolder(bin_folder(mp))
    got = mp.ImportMedia([path]) or []
    mp.SetCurrentFolder(prev)
    return got[0] if got else None


def takes(item):
    n = item.GetTakesCount() or 0
    out = []
    for i in range(1, n + 1):
        t = item.GetTakeByIndex(i) or {}
        m = t.get("mediaPoolItem")
        out.append((i, m.GetClipProperty("File Path") if m else ""))
    return out


def cleaned_take(item):
    for i, p in takes(item):
        if is_cleaned(p):
            return i
    return 0


def original_take(item):
    for i, p in takes(item):
        if p and not is_cleaned(p):
            return i
    return 0


def add_clean_take(mp, item, cleaned, first):
    """Put the cleaned file on this timeline clip as a take (and select it)."""
    src = src_of(item)
    a, b = used_range(item)
    old = cleaned_take(item)
    if old:
        item.DeleteTakeByIndex(old)
    mpi = import_file(mp, cleaned)
    if not mpi:
        return False, "could not import " + cleaned
    ok = item.AddTake(mpi, a - first, b - first)
    if not ok:
        return False, "Resolve refused the take"
    idx = cleaned_take(item)
    if idx:
        item.SelectTakeByIndex(idx)
    try:
        item.SetClipColor("Teal")
    except Exception:
        pass
    return True, os.path.basename(src)


def start_jobs(jobs):
    """Write a job list next to the first clip's trip and clean in a background window. Returns the log path."""
    d = clean_dir(jobs[0]["file"])
    os.makedirs(d, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    jp = os.path.join(d, "jobs_%s.json" % ts)
    json.dump({"jobs": jobs, "made": ts}, open(jp, "w", encoding="utf-8"), indent=1)
    logp = jp[:-5] + "_log.txt"
    bat = os.path.join(d, "clean_%s.bat" % ts)
    with open(bat, "w", encoding="utf-8") as fh:
        fh.write('@echo off\nchcp 65001 >nul\nset PYTHONIOENCODING=utf-8\ntitle SPP Reflection cleaning\n'
                 '"%s" "%s" jobs "%s"\necho.\necho You can close this window.\npause >nul\n' % (C.PY, ENGINE, jp))
    subprocess.Popen('start "SPP Reflection cleaning" cmd /c "%s"' % bat, shell=True)
    return logp


def estimate_minutes(jobs):
    secs = sum((j["out"] - j["in"] + 1) / j.get("fps", 30.0) for j in jobs)
    return max(1, int(round(secs * 4.5 / 60 + 0.4 * len(jobs))))
