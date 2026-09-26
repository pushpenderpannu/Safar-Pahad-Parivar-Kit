"""Shared SFX helpers for the Safar Pahad Parivar Resolve menu scripts (runs inside Resolve's Python)."""
import json, os, re
import spp_resolve_common as C

SFX_DIR = os.path.join(C.KIT, "SFX")
BIN = "SPP SFX"
AUTO_COLOR = "Lime"          # clips placed by 'SFX - Auto Sound for Titles' get this colour


def catalog():
    p = os.path.join(SFX_DIR, "sfx_catalog.json")
    if not os.path.exists(p):
        print("The SFX library isn't built yet. In PowerShell (kit folder) run:  .\\Tools\\make_sfx.ps1")
        return None
    return json.load(open(p, encoding="utf-8"))


def _sub(mp, parent, name):
    for f in parent.GetSubFolderList():
        if f.GetName() == name:
            return f
    return mp.AddSubFolder(parent, name)


class Pool:
    """Finds / imports library files into the 'SPP SFX' bin (one sub-bin per category)."""

    def __init__(self, proj):
        self.proj = proj
        self.mp = proj.GetMediaPool()
        self.root = _sub(self.mp, self.mp.GetRootFolder(), BIN)
        self.cache = {}
        for f in self.root.GetSubFolderList():
            for c in f.GetClipList() or []:
                self.cache[os.path.normcase(c.GetClipProperty("File Path") or "")] = c

    def get(self, rel):
        path = os.path.join(SFX_DIR, rel)
        key = os.path.normcase(path)
        if key in self.cache:
            return self.cache[key]
        if not os.path.exists(path):
            return None
        cat = rel.replace("\\", "/").split("/")[0]
        prev = self.mp.GetCurrentFolder()
        self.mp.SetCurrentFolder(_sub(self.mp, self.root, cat))
        items = self.mp.ImportMedia([path]) or []
        self.mp.SetCurrentFolder(prev)
        if items:
            self.cache[key] = items[0]
            return items[0]
        return None

    def import_all(self, entries):
        by = {}
        for e in entries:
            key = os.path.normcase(os.path.join(SFX_DIR, e["file"]))
            if key not in self.cache:
                by.setdefault(e["category"], []).append(os.path.join(SFX_DIR, e["file"]))
        prev, n = self.mp.GetCurrentFolder(), 0
        for cat, files in sorted(by.items()):
            self.mp.SetCurrentFolder(_sub(self.mp, self.root, cat))
            n += len(self.mp.ImportMedia(files) or [])
        self.mp.SetCurrentFolder(prev)
        return n


def clip_frames(mpi, fps):
    """Length of a media-pool clip in timeline frames."""
    try:
        f = int(mpi.GetClipProperty("Frames"))
        if f > 0:
            return f
    except Exception:
        pass
    h, m, s, f = [int(x) for x in re.split("[:;]", mpi.GetClipProperty("Duration") or "00:00:01:00")]
    return int(round(((h * 60 + m) * 60 + s) * fps + f))


def sfx_tracks(tl):
    """Audio tracks meant for sound effects (named 'SFX ...'), in order."""
    return [i for i in range(1, tl.GetTrackCount("audio") + 1) if (tl.GetTrackName("audio", i) or "").upper().startswith("SFX")]


def busy(tl, track, a, b):
    return any(it.GetStart() < b and a < it.GetEnd() for it in (tl.GetItemListInTrack("audio", track) or []))


def append(proj, tl, mpi, track, rec, start=0, length=None, fps=30.0):
    n = clip_frames(mpi, fps) - start if length is None else length
    res = proj.GetMediaPool().AppendToTimeline([{"mediaPoolItem": mpi, "startFrame": start, "endFrame": start + max(1, n),
                                                "trackIndex": track, "recordFrame": rec, "mediaType": 2}]) or []
    return res


def free_track(tl, tracks, a, b):
    """First SFX track free in [a, b); adds a new 'SFX n' track when all are busy."""
    for tr in tracks:
        if not busy(tl, tr, a, b):
            return tr
    tl.AddTrack("audio", "stereo")
    tr = tl.GetTrackCount("audio")
    tl.SetTrackName("audio", tr, "SFX %d" % (len(tracks) + 1))
    tracks.append(tr)
    return tr


def loop_fill(proj, tl, mpi, track, a, b, fps):
    """Repeat a loop clip from frame a to frame b (last copy trimmed). Returns the placed items."""
    n = clip_frames(mpi, fps)
    out, t = [], a
    while t < b:
        ln = min(n, b - t)
        out += append(proj, tl, mpi, track, t, 0, ln, fps)
        t += ln
    return out


def ask_choice(resolve, title, label, options, default=0, bmd_=None):
    """Small window with one drop-down. Returns the chosen option (or the default if no UI)."""
    try:
        fu = resolve.Fusion()
        ui = fu.UIManager
        if bmd_ is None:
            import builtins
            bmd_ = getattr(builtins, "bmd", None)
        disp = bmd_.UIDispatcher(ui)
        win = disp.AddWindow({"ID": "Q", "WindowTitle": title, "Geometry": [500, 300, 380, 120]},
                             ui.VGroup([ui.Label({"Text": label}), ui.ComboBox({"ID": "c"}),
                                        ui.HGroup([ui.Button({"ID": "ok", "Text": "OK"}), ui.Button({"ID": "cancel", "Text": "Cancel"})])]))
        it = win.GetItems()
        for o in options:
            it["c"].AddItem(o)
        it["c"].CurrentIndex = default
        res = {}

        def done(ok):
            if ok:
                res["v"] = options[it["c"].CurrentIndex]
            disp.ExitLoop()
        win.On.ok.Clicked = lambda ev: done(True)
        win.On.cancel.Clicked = lambda ev: done(False)
        win.On.Q.Close = lambda ev: done(False)
        win.Show(); disp.RunLoop(); win.Hide()
        return res.get("v")
    except Exception as e:
        print("(no dialog: %s) using '%s'" % (e, options[default]))
        return options[default]
