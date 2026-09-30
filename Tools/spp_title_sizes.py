"""One size setting per SPP title type (Info Card, Film Title, Chapter ...).

    - set_timeline(tl, file, size): every title of that type on the timeline gets that Size
    - saved sizes live in <kit>\\Settings\\title_sizes.json and become the default Size of NEW titles you drag in
      (written into the installed templates; Resolve picks it up after a restart; install.ps1 re-applies it)

    python spp_title_sizes.py apply-defaults      (run by install.ps1)
"""
import json, os, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVED = os.path.join(KIT, "Settings", "title_sizes.json")
INSTALLED = os.path.join(os.environ.get("APPDATA", ""), r"Blackmagic Design\DaVinci Resolve\Support\Fusion\Templates\Edit\Titles\Safar Pahad Parivar")
KIT_TPL = os.path.join(KIT, r"Resolve\Templates\Edit\Titles\Safar Pahad Parivar")
NAMES = {"SPP-Info-Card": "Info Card", "SPP-Film-Title": "Film Title", "SPP-Chapter": "Chapter",
         "SPP-Altitude-Counter": "Altitude Counter", "SPP-Peak-Callout": "Peak Callout",
         "SPP-Popup-Title": "Pop-up Title", "SPP-Captions": "Captions"}


def _tpl_dir():
    return INSTALLED if os.path.isdir(INSTALLED) else KIT_TPL


def size_info(file):
    """(DynParamNum index, key, template default, min, max) of the Size setting, or None."""
    p = os.path.join(_tpl_dir(), file + ".ograf.json")
    if not os.path.exists(p):
        p = os.path.join(KIT_TPL, file + ".ograf.json")
    try:
        props = json.load(open(p, encoding="utf-8"))["schema"]["properties"]
    except Exception:
        return None
    keys = list(props)
    for k in ("scale", "size"):
        if k in props:
            d = props[k]
            return keys.index(k), k, float(d.get("default", 1.0)), float(d.get("minimum", 0.3)), float(d.get("maximum", 2.0))
    return None


def load_saved():
    try:
        return {k: float(v) for k, v in json.load(open(SAVED, encoding="utf-8")).items()}
    except Exception:
        return {}


def save(sizes):
    os.makedirs(os.path.dirname(SAVED), exist_ok=True)
    cur = load_saved()
    cur.update({k: round(float(v), 3) for k, v in sizes.items()})
    json.dump(cur, open(SAVED, "w", encoding="utf-8"), indent=1)


def apply_defaults(sizes=None):
    """Write saved sizes as the 'Size' default into the installed templates (new titles). Returns files changed."""
    sizes = load_saved() if sizes is None else sizes
    done = []
    for file, v in sizes.items():
        p = os.path.join(INSTALLED, file + ".ograf.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        props = d["schema"]["properties"]
        k = "scale" if "scale" in props else ("size" if "size" in props else None)
        if k and abs(float(props[k].get("default", 1)) - v) > 1e-6:
            props[k]["default"] = v
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            done.append(file)
    return done


def loader(item):
    c = item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else None
    if not c:
        return None
    for t in c.GetToolList(False).values():
        if t.GetAttrs("TOOLS_RegID") == "OGrafLoader":
            return t
    return None


def scan(tl):
    """{file: [(item, loader, current size), ...]} for SPP titles on the timeline."""
    out = {}
    for tr in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", tr) or []:
            n = it.GetName()
            if n not in NAMES:
                continue
            info = size_info(n)
            t = loader(it) if info else None
            if t is None:
                continue
            v = t.GetInput("DynParamNum%d" % info[0])
            out.setdefault(n, []).append((it, t, float(v if v is not None else info[2])))
    return out


def set_timeline(found, file, size):
    info = size_info(file)
    n = 0
    for it, t, cur in found.get(file, []):
        if abs(cur - size) > 1e-6:
            t.SetInput("DynParamNum%d" % info[0], float(size))
            n += 1
    return n


if __name__ == "__main__":
    if "apply-defaults" in sys.argv:
        ch = apply_defaults()
        if ch:
            print("Title sizes: defaults set for " + ", ".join(NAMES.get(f, f) for f in ch))
