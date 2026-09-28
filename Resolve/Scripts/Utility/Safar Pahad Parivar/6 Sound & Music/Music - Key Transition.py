# Safar Pahad Parivar - key-matched music transition.
# Select TWO music clips on the timeline (the one ending and the one starting) -> it listens to the end of the first
# and the start of the second, finds their musical keys, and places a transition on a free SFX track so its big moment
# lands exactly where the new music starts:  Bridge (old key -> new key), Swell into the new key, or Tail + Swell.
# Select ONE music clip -> Swell into it (lands on its first frame) or Tail at its end.
# Keys can be changed in the window before it builds.  Uses the library file when one exists, otherwise makes one.
import json, os, subprocess, sys, time
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

NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KEYS = NAMES + [n + "m" for n in NAMES]
TOOL = os.path.join(C.KIT, r"Tools\spp_key.py")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def detect(item, fps, end):
    """Key of the first (end=False) or last (end=True) 20 s of the clip as it is used on the timeline."""
    src = item.GetMediaPoolItem().GetClipProperty("File Path")
    left = (item.GetLeftOffset() or 0) / fps
    used = (item.GetEnd() - item.GetStart()) / fps
    dur = min(20.0, used)
    start = left + used - dur if end else left
    r = subprocess.run([C.PY, TOOL, src, "--start", "%.2f" % start, "--dur", "%.2f" % dur, "--json"], capture_output=True,
                       text=True, env=ENV, creationflags=0x08000000)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        print("key detection failed:", r.stderr[-300:])
        return {"key": "D", "confidence": 0, "also": []}


def ask(ka, kb, two):
    modes = (["Bridge: old key -> new key (5 s, lands on the cut)", "Swell into the new key (3 s)",
              "Tail of the old key + swell into the new"] if two else ["Swell into this music (lands on its start)", "Tail at the end of this music"])
    try:
        ui = resolve.Fusion().UIManager
        disp = bmd.UIDispatcher(ui)
        rows = [ui.Label({"Text": "Detected:  %s%s" % ("%s (%.2f, also %s)  ->  " % (ka["key"], ka["confidence"], ", ".join(k for k, _ in ka["also"][:2])) if ka else "",
                                                     "%s (%.2f, also %s)" % (kb["key"], kb["confidence"], ", ".join(k for k, _ in kb["also"][:2])) if kb else "")})]
        if ka:
            rows += [ui.HGroup([ui.Label({"Text": "Old key"}), ui.ComboBox({"ID": "ka"})])]
        if kb:
            rows += [ui.HGroup([ui.Label({"Text": "New key"}), ui.ComboBox({"ID": "kb"})])]
        rows += [ui.ComboBox({"ID": "mode"}), ui.HGroup([ui.Label({"Text": "Variation"}), ui.ComboBox({"ID": "v"})]),
                 ui.HGroup([ui.Button({"ID": "ok", "Text": "Place transition"}), ui.Button({"ID": "cancel", "Text": "Cancel"})])]
        win = disp.AddWindow({"ID": "KT", "WindowTitle": "SPP Key Transition", "Geometry": [480, 280, 520, 220]}, ui.VGroup(rows))
        it = win.GetItems()
        for cid, k in (("ka", ka), ("kb", kb)):
            if k:
                for n in KEYS:
                    it[cid].AddItem(n)
                it[cid].CurrentIndex = KEYS.index(k["key"]) if k["key"] in KEYS else 2
        for m in modes:
            it["mode"].AddItem(m)
        for v in ("1", "2", "3"):
            it["v"].AddItem(v)
        res = {}

        def done(ev, ok):
            if ok:
                res.update(ka=KEYS[it["ka"].CurrentIndex] if ka else None, kb=KEYS[it["kb"].CurrentIndex] if kb else None,
                           mode=it["mode"].CurrentIndex, v=it["v"].CurrentIndex)
            disp.ExitLoop()
        win.On.ok.Clicked = lambda ev: done(ev, True)
        win.On.cancel.Clicked = lambda ev: done(ev, False)
        win.On.KT.Close = lambda ev: done(ev, False)
        win.Show(); disp.RunLoop(); win.Hide()
        return res or None
    except Exception as e:
        print("(no dialog: %s) using the detected keys" % e)
        return {"ka": ka and ka["key"], "kb": kb and kb["key"], "mode": 0, "v": 0}


def sound(kind, ka, kb, v):
    """(path, land seconds): library file if it exists, else render one into SFX\\_transitions."""
    lib = os.path.join(C.KIT, "SFX", "19 Music Transitions")
    name = {"swell": "Swell_Into_%s" % kb, "tail": "Tail_%s" % ka, "bridge": "Bridge_%s_to_%s" % (ka, kb)}[kind]
    land = {"swell": 3.0, "tail": 0.0, "bridge": 4.0}[kind]
    for vv in (v + 1, 1):
        p = os.path.join(lib, "SPP_%s_v%02d.wav" % (name, vv))
        if os.path.exists(p):
            return p, land
    outd = os.path.join(C.KIT, "SFX", "_transitions")
    os.makedirs(outd, exist_ok=True)
    out = os.path.join(outd, "SPP_%s_v%02d.wav" % (name, v + 1))
    if not os.path.exists(out):
        print("Making %s ..." % name)
        keys = {"swell": [kb], "tail": [ka], "bridge": [ka, kb]}[kind]
        r = subprocess.run([C.PY, TOOL, "render", kind] + keys + ["--v", str(min(v, 2 if kind == "swell" else 1)), "--out", out],
                           capture_output=True, text=True, env=ENV, creationflags=0x08000000)
        if r.returncode != 0:
            print("FAILED:", r.stderr[-500:]); return None, land
    return out, land


def place(proj, tl, path, at_frame, land, fps, tracks):
    mp = proj.GetMediaPool()
    root = mp.GetRootFolder()
    b = S._sub(mp, S._sub(mp, root, S.BIN), "19 Music Transitions")
    prev = mp.GetCurrentFolder(); mp.SetCurrentFolder(b)
    m = (mp.ImportMedia([path]) or [None])[0]
    mp.SetCurrentFolder(prev)
    if not m:
        print("import failed", path); return
    a = max(tl.GetStartFrame(), at_frame - int(round(land * fps)))
    tr = S.free_track(tl, tracks, a, a + S.clip_frames(m, fps))
    S.append(proj, tl, m, tr, a, fps=fps)
    print("%s -> %s at %s" % (os.path.basename(path), tl.GetTrackName("audio", tr), tl.GetCurrentTimecode()))


def main():
    proj = resolve.GetProjectManager().GetCurrentProject()
    tl = proj.GetCurrentTimeline() if proj else None
    if not tl or not C.engine_ok():
        print("Open a timeline first."); return
    sel = sorted([it for it in (tl.GetSelectedClips() or []) if it.GetTrackTypeAndIndex()[0] == "audio" and it.GetMediaPoolItem()],
                 key=lambda it: it.GetStart())
    if not sel or len(sel) > 2:
        print("Select one or two MUSIC clips on the timeline (the ending one and the starting one)."); return
    fps = float(tl.GetSetting("timelineFrameRate"))
    tracks = S.sfx_tracks(tl)
    if not tracks:
        tl.AddTrack("audio", "stereo"); tracks = [tl.GetTrackCount("audio")]; tl.SetTrackName("audio", tracks[0], "SFX 1")
    if len(sel) == 2:
        out_, in_ = sel
        ka, kb = detect(out_, fps, True), detect(in_, fps, False)
        opt = ask(ka, kb, True)
        if not opt:
            return
        cut = in_.GetStart()
        if opt["mode"] == 0:
            p, land = sound("bridge", opt["ka"], opt["kb"], opt["v"])
            if p: place(proj, tl, p, cut, land, fps, tracks)
        else:
            if opt["mode"] == 2:
                p, land = sound("tail", opt["ka"], None, opt["v"])
                if p: place(proj, tl, p, out_.GetEnd() - int(1.0 * fps), land, fps, tracks)
            p, land = sound("swell", None, opt["kb"], opt["v"])
            if p: place(proj, tl, p, cut, land, fps, tracks)
    else:
        it = sel[0]
        kb = detect(it, fps, False)
        opt = ask(None, kb, False)
        if not opt:
            return
        if opt["mode"] == 0:
            p, land = sound("swell", None, opt["kb"], opt["v"])
            if p: place(proj, tl, p, it.GetStart(), land, fps, tracks)
        else:
            ke = detect(it, fps, True)
            p, land = sound("tail", ke["key"], None, opt["v"])
            if p: place(proj, tl, p, it.GetEnd() - int(1.0 * fps), land, fps, tracks)


main()
