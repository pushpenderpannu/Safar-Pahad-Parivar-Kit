"""Shared helpers for the Safar Pahad Parivar Resolve menu scripts (runs inside Resolve's Python)."""
import json, os, subprocess

HERE = os.path.join(os.environ.get("APPDATA", ""), r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Safar Pahad Parivar")


def kit_dir():
    kit = r"F:\Video Editing\_Safar Pahad Parivar Kit"
    try:
        with open(os.path.join(HERE, "kit_path.txt"), encoding="utf-8-sig") as fh:
            kit = fh.read().strip() or kit
    except Exception:
        pass
    return kit


KIT = kit_dir()
PY = os.path.join(KIT, r"Tools\.venv\Scripts\python.exe")
GPS = os.path.join(KIT, r"Tools\spp_gps.py")
INDEX = "_spp_gps_index.json"


def engine_ok():
    if os.path.exists(PY):
        return True
    print("The kit's Python tools are not installed. In PowerShell run:\n  " + os.path.join(KIT, r"Tools\setup_word_timing.ps1"))
    return False


def run_gps(*args):
    """Run spp_gps.py in the kit venv; returns (stdout, stderr, returncode)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([PY, GPS] + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, creationflags=0x08000000)
    return r.stdout, r.stderr, r.returncode


def trip_of(path):
    """Trip folder for a media file: the folder holding 'Footage' (or an existing GPS index)."""
    d = os.path.dirname(path)
    while d and os.path.dirname(d) != d:
        if os.path.exists(os.path.join(d, INDEX)) or os.path.isdir(os.path.join(d, "Footage")):
            return d
        d = os.path.dirname(d)
    return None


def ensure_index(trip):
    if not os.path.exists(os.path.join(trip, INDEX)):
        print("Building the GPS index for this trip (first time only, ~1 minute)...")
        out, err, rc = run_gps("index", trip)
        print(err[-600:])
        return rc == 0
    return True


def templates_on(tl, name):
    """[(timeline item, OGrafLoader tool)] for every OGraf title of this template on the timeline."""
    found = []
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            try:
                if not it.GetFusionCompCount():
                    continue
                for tool in (it.GetFusionCompByIndex(1).GetToolList(False) or {}).values():
                    if name in str(tool.GetInput("TemplatePath") or ""):
                        found.append((it, tool, t))
            except Exception:
                pass
    return found


def media_under(tl, frame, above_track):
    """The footage clip visible at 'frame' below the given video track (top-most first)."""
    for t in range(above_track - 1, 0, -1):
        for it in tl.GetItemListInTrack("video", t) or []:
            if it.GetStart() <= frame < it.GetEnd():
                mpi = it.GetMediaPoolItem()
                path = mpi.GetClipProperty("File Path") if mpi else ""
                if path and os.path.exists(path):
                    return it, path
    return None, None


def footage_on(tl):
    """All footage file paths used on the timeline's video tracks."""
    paths = set()
    for t in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", t) or []:
            mpi = it.GetMediaPoolItem()
            p = mpi.GetClipProperty("File Path") if mpi else ""
            if p and os.path.exists(p):
                paths.add(p)
    return sorted(paths)


def set_dyn(tool, index, value):
    """Set an OGraf title setting by its position in the template (Resolve names them DynParam*<n>)."""
    if isinstance(value, bool):
        tool.SetInput(f"DynParamCheck{index}", 1 if value else 0)
    elif isinstance(value, (int, float)):
        tool.SetInput(f"DynParamNum{index}", value)
    else:
        tool.SetInput(f"DynParamText{index}", value)


def set_select(tool, index, value):
    """Dropdowns: write both forms (text and number) - whichever the loader uses."""
    tool.SetInput(f"DynParamText{index}", str(int(value)))
    tool.SetInput(f"DynParamNum{index}", int(value))
